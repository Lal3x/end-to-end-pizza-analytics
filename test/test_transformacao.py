"""Testes sintéticos de specs/transformacao.md com DuckDB temporário real."""

from decimal import Decimal

import duckdb
import pandas as pd
import pytest

import db
from pipeline import transformacao as t


@pytest.fixture
def fontes():
    """Um pedido de duas unidades iguais exercita multiplicidade e dinheiro."""
    return {
        "orders": pd.DataFrame(
            [[1, "C1", "S1", "2020-01-02T12:30Z", 2, 21.98]],
            columns=t.FONTES["orders"]["colunas"],
        ),
        "order_items": pd.DataFrame(
            [["PZ026", 1], ["PZ026", 1]], columns=t.FONTES["order_items"]["colunas"]
        ),
        "customers": pd.DataFrame(
            [["C1", "-23.5", "-46.6"]], columns=t.FONTES["customers"]["colunas"]
        ),
        "stores": pd.DataFrame(
            [["S1", "00123", "SP", "-23.5", "-46.6", "Cidade", "Estado", "1.2"]],
            columns=t.FONTES["stores"]["colunas"],
        ),
        "products": pd.DataFrame(
            [["PZ026", "Pizza", "10.99", "Classic", "Small", None, "2020-01-01,"]],
            columns=t.FONTES["products"]["colunas"],
        ),
    }


def preparar(caminho, fontes):
    """Grava somente as fontes sintéticas, sem usar o banco do projeto."""
    with duckdb.connect(str(caminho)) as con:
        db.criar_schema(con, "raw")
        for nome, df in fontes.items():
            db.gravar(con, df, "raw", nome)


def test_publicacao_tipos_preservacao_reexecucao(tmp_path, fontes):
    caminho = tmp_path / "teste.duckdb"
    preparar(caminho, fontes)
    for _ in range(2):
        relatorio = t.executar(caminho)
        assert relatorio["validacoes"]["pedidos_divergentes"] == 0
        assert relatorio["tabelas"]["order_items"]["repeticoes_preservadas"] == 1
        with duckdb.connect(str(caminho)) as con:
            assert con.sql("select total from refined.orders").fetchone() == (
                Decimal("21.98"),
            )
            assert con.sql("select count(*) from refined.order_items").fetchone() == (
                2,
            )
            assert con.sql("select zipcode from refined.stores").fetchone() == (
                "00123",
            )
            assert con.sql("select Launch from raw.products").fetchone() == (
                "2020-01-01,",
            )
            tipos = dict(
                (r[0], r[1]) for r in con.sql("describe refined.orders").fetchall()
            )
            assert tipos["id"] == "VARCHAR"
            assert tipos["nItems"] == "INTEGER"
            assert tipos["total"] == "DECIMAL(18,2)"
            assert tipos["order_date"] == "DATE"
            assert tipos["order_timestamp"] == "TIMESTAMP WITH TIME ZONE"


def test_precisoes_temporais_sem_inventar_hora(fontes):
    df = pd.concat([fontes["orders"]] * 3, ignore_index=True)
    df["id"] = [1, 2, 3]
    df["orderDate"] = ["2020-02-29", "2020-02-29T12:34Z", "2020-02-29T12:34:56Z"]
    resultado, _ = t.transformar("orders", df)
    assert resultado["timestamp_precision"].tolist() == ["date", "minute", "second"]
    assert pd.isna(resultado.loc[0, "order_timestamp"])
    assert resultado.loc[1, "order_timestamp"] == pd.Timestamp("2020-02-29T12:34:00Z")
    assert resultado.loc[2, "order_timestamp"].second == 56
    assert resultado["orderDate"].tolist() == df["orderDate"].tolist()


@pytest.mark.parametrize(
    "valor", ["2020-02-30", "2020-01-01 12:30", "2020-01-01T12:30:00+00:00"]
)
def test_datas_invalidas_falham(fontes, valor):
    fontes["orders"].loc[0, "orderDate"] = valor
    with pytest.raises(ValueError):
        t.transformar("orders", fontes["orders"])


@pytest.mark.parametrize(
    "valor", ["1.001", "-1", "NaN", "inf", "10000000000000000", " 1.00"]
)
def test_preco_invalido_nao_arredonda(valor):
    with pytest.raises(ValueError):
        t.dinheiro(pd.Series([valor]), "products.Price")


@pytest.mark.parametrize("valor", [1.001, -1.0, float("nan"), float("inf"), 1e16])
def test_total_invalido_falha(valor):
    with pytest.raises(ValueError):
        t.dinheiro(pd.Series([valor]), "orders.total", binario=True)


def test_ruido_binario_preserva_centavos():
    assert t.dinheiro(pd.Series([0.1 + 0.2]), "total", True).tolist() == [
        Decimal("0.30")
    ]


def test_duplicatas_exatas_removidas_conflitos_falham(fontes):
    df = pd.concat([fontes["products"]] * 2, ignore_index=True)
    resultado, relatorio = t.transformar("products", df)
    assert len(resultado) == 1
    assert relatorio["duplicatas_removidas"] == 1
    df.loc[1, "Price"] = "11.00"
    with pytest.raises(ValueError, match="conflito"):
        t.transformar("products", df)


@pytest.mark.parametrize(
    "nome,coluna,valor",
    [
        ("orders", "customerId", ""),
        ("orders", "storeId", None),
        ("orders", "nItems", 0),
        ("orders", "nItems", 1.5),
        ("customers", "latitude", "91"),
        ("customers", "longitude", "inf"),
        ("products", "Size", "Novo"),
        ("products", "Category", "Nova"),
        ("products", "Launch", "2020-01-01,,"),
        ("products", "Launch", "2020-02-30"),
        ("products", "SKU", "PZ999"),
    ],
)
def test_dominios_nulos_e_correcao_restrita(fontes, nome, coluna, valor):
    df = fontes[nome].astype(object)
    df.loc[0, coluna] = valor
    with pytest.raises(ValueError):
        t.transformar(nome, df)


@pytest.mark.parametrize("alteracao", ["fk", "quantidade", "dinheiro", "conversao"])
def test_falha_restaura_refined_anterior(tmp_path, fontes, alteracao):
    caminho = tmp_path / "teste.duckdb"
    preparar(caminho, fontes)
    t.executar(caminho)
    with duckdb.connect(str(caminho)) as con:
        comando = {
            "fk": "update raw.orders set customerId='ausente'",
            "quantidade": (
                "delete from raw.order_items where rowid="
                "(select min(rowid) from raw.order_items)"
            ),
            "dinheiro": "update raw.orders set total=22.00",
            "conversao": "update raw.products set Price='10.999'",
        }[alteracao]
        con.execute(comando)
    with pytest.raises(ValueError):
        t.executar(caminho)
    with duckdb.connect(str(caminho)) as con:
        assert con.sql("select total from refined.orders").fetchone() == (
            Decimal("21.98"),
        )
        assert con.sql("select count(*) from refined.order_items").fetchone() == (2,)


def test_banco_ausente_nao_cria_arquivo(tmp_path):
    caminho = tmp_path / "ausente.duckdb"
    with pytest.raises(ValueError, match="Banco ausente"):
        t.executar(caminho)
    assert not caminho.exists()


def test_total_maior_fora_da_amostra_nao_depende_de_inferencia(tmp_path, fontes):
    fontes["orders"] = pd.concat([fontes["orders"]] * 1500, ignore_index=True)
    fontes["orders"]["id"] = range(1, 1501)
    fontes["orders"].loc[1499, ["nItems", "total"]] = [10, 109.90]
    fontes["order_items"] = pd.DataFrame(
        [("PZ026", i) for i in range(1, 1501) for _ in range(10 if i == 1500 else 2)],
        columns=["SKU", "orderID"],
    )
    caminho = tmp_path / "amostra.duckdb"
    preparar(caminho, fontes)
    t.executar(caminho)
    with duckdb.connect(str(caminho)) as con:
        assert con.sql(
            "select total from refined.orders where id='1500'"
        ).fetchone() == (Decimal("109.90"),)
