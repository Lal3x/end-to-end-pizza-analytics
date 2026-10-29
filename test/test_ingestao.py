"""Pizza Paradise: fontes sintéticas, Parquets e DuckDB reais temporários."""

import csv

import duckdb
import pandas as pd
import pytest

import db
from pipeline import ingestao
from pipeline.ingestao import FONTES


def preparar(tmp_path, monkeypatch):
    """Dois pedidos; o primeiro compra duas ocorrências idênticas de P01."""
    pasta = tmp_path / "raw" / "pizza_paradise"
    pasta.mkdir(parents=True)
    monkeypatch.setattr(db, "PASTA_RAW", tmp_path / "raw")
    monkeypatch.setattr("sys.argv", ["ingestao"])
    linhas = {
        "customers": [["C01", "-23.0", "-46.0"], ["C02", "-22.0", "-45.0"]],
        "stores": [["S01", "00123", "CA", "35.0", "-120.0", "Ação", "CA", "1.5"]],
        "products": [
            [
                "P01",
                "Pizza",
                "12.50",
                "Classic",
                "Small",
                "tomate, queijo\n fresco",
                "2020-01-01",
            ],
            ["P02", "Pizza", "7.25", "Classic", "Medium", "queijo", "2020-01-01,"],
        ],
    }
    for nome, registros in linhas.items():
        with (pasta / FONTES[nome]["arquivo"]).open(
            "w", encoding="utf-8", newline=""
        ) as f:
            escritor = csv.writer(f)
            escritor.writerow(FONTES[nome]["colunas"])
            escritor.writerows(registros)
    pd.DataFrame(
        {
            "id": pd.Series([0, 1], dtype="int32"),
            "customerId": ["C01", "C02"],
            "storeId": ["S01", "S01"],
            "orderDate": ["2022-01-01T12:00:00Z", "2022-01-02"],
            "nItems": pd.Series([2, 1], dtype="int32"),
            "total": [25.0, 7.25],
        }
    ).to_parquet(pasta / "orders.parquet", index=False)
    pd.DataFrame(
        {
            "SKU": ["P01", "P01", "P02"],
            "orderID": pd.Series([0, 0, 1], dtype="int32"),
        }
    ).to_parquet(pasta / "order_items.parquet", index=False)
    return pasta


def test_preserva_valores_tipos_e_ocorrencias_na_reexecucao(tmp_path, monkeypatch):
    preparar(tmp_path, monkeypatch)
    esperado = {
        "orders": 2,
        "order_items": 3,
        "customers": 2,
        "stores": 1,
        "products": 2,
    }
    assert ingestao.executar() == esperado
    assert ingestao.executar() == esperado
    with duckdb.connect(str(tmp_path / "pizza.duckdb"), read_only=True) as con:
        assert con.execute(
            "SELECT * FROM raw.order_items ORDER BY orderID"
        ).fetchall() == [("P01", 0), ("P01", 0), ("P02", 1)]
        assert con.execute("SELECT zipcode,city FROM raw.stores").fetchone() == (
            "00123",
            "Ação",
        )
        assert con.execute(
            "SELECT Price,Ingredients FROM raw.products WHERE SKU='P01'"
        ).fetchone() == ("12.50", "tomate, queijo\n fresco")
        assert con.execute(
            "SELECT Launch FROM raw.products WHERE SKU='P02'"
        ).fetchone() == ("2020-01-01,",)
        for nome in ("orders", "order_items"):
            assert [
                r[1] for r in con.execute(f"DESCRIBE raw.{nome}").fetchall()
            ] == FONTES[nome]["tipos"]
        assert con.execute(
            "SELECT DISTINCT data_type FROM information_schema.columns "
            "WHERE table_schema='raw' "
            "AND table_name IN ('customers','stores','products')"
        ).fetchall() == [("VARCHAR",)]


def test_preserva_nulos_tokens_espacos_e_repeticoes_csv(tmp_path, monkeypatch):
    pasta = preparar(tmp_path, monkeypatch)
    cabecalho = ",".join(FONTES["products"]["colunas"])
    # Coluna Ingredients inteiramente nula e repetição intencional preservada.
    (pasta / "products.csv").write_text(
        cabecalho + "\nP01,NA,12.50,NULL,Small,,2020-01-01\n"
        "P01,NA,12.50,NULL,Small,,2020-01-01\n"
        "P02,N/A,7.25,  Classic  ,Medium,,2020-01-01\n",
        encoding="utf-8",
    )
    assert ingestao.executar()["products"] == 3
    with duckdb.connect(str(tmp_path / "pizza.duckdb"), read_only=True) as con:
        assert con.execute(
            "SELECT Name,Category,Ingredients FROM raw.products ORDER BY SKU"
        ).fetchall() == [
            ("NA", "NULL", None),
            ("NA", "NULL", None),
            ("N/A", "  Classic  ", None),
        ]
        assert con.execute("DESCRIBE raw.products").fetchall()[5][1] == "VARCHAR"


def test_fonte_ausente_falha_antes_de_criar_banco(tmp_path, monkeypatch):
    pasta = preparar(tmp_path, monkeypatch)
    (pasta / "orders.parquet").unlink()
    with pytest.raises(ValueError, match="orders.parquet"):
        ingestao.executar()
    assert ingestao.main() == 1
    assert not (tmp_path / "pizza.duckdb").exists()


@pytest.mark.parametrize(
    "conteudo",
    [
        "errado,latitude,longitude\nC01,1,2\n",
        "id,latitude,longitude\nC01,1\n",
        "id,latitude,longitude\nC01,1,2,extra\n",
        "id,latitude,longitude\n\n",
        'id,latitude,longitude\nC01,"sem fim',
    ],
)
def test_csv_invalido_preserva_raw_anterior(tmp_path, monkeypatch, conteudo):
    pasta = preparar(tmp_path, monkeypatch)
    ingestao.executar()
    (pasta / "customers.csv").write_text(conteudo, encoding="utf-8")
    with pytest.raises(ValueError, match="customers.csv"):
        ingestao.executar()
    with duckdb.connect(str(tmp_path / "pizza.duckdb"), read_only=True) as con:
        assert con.execute("SELECT count(*) FROM raw.orders").fetchone() == (2,)


def test_encoding_invalido_falha_sem_banco(tmp_path, monkeypatch):
    pasta = preparar(tmp_path, monkeypatch)
    (pasta / "customers.csv").write_bytes(b"id,latitude,longitude\n\xff,1,2\n")
    with pytest.raises(ValueError, match="customers.csv"):
        ingestao.executar()
    assert not (tmp_path / "pizza.duckdb").exists()


@pytest.mark.parametrize("tipo", ["arquivo", "colunas", "tipos"])
def test_parquet_invalido_e_schema_incompativel_falham_antes_do_banco(
    tmp_path, monkeypatch, tipo
):
    pasta = preparar(tmp_path, monkeypatch)
    if tipo == "arquivo":
        (pasta / "orders.parquet").write_bytes(b"nao e parquet")
    elif tipo == "colunas":
        pd.DataFrame({"errado": [1]}).to_parquet(pasta / "orders.parquet", index=False)
    else:
        df = pd.read_parquet(pasta / "orders.parquet")
        df["id"] = df["id"].astype("int64")
        df.to_parquet(pasta / "orders.parquet", index=False)
    with pytest.raises(ValueError, match="orders.parquet"):
        ingestao.executar()
    assert not (tmp_path / "pizza.duckdb").exists()


def test_substitui_schema_antigo_e_permite_destino_separado(tmp_path, monkeypatch):
    preparar(tmp_path, monkeypatch)
    destino = tmp_path / "ensaio" / "novo.duckdb"
    destino.parent.mkdir()
    with duckdb.connect(str(destino)) as con:
        con.execute("CREATE SCHEMA raw")
        con.execute("CREATE TABLE raw.order_details AS SELECT 7 AS legado")
    assert ingestao.executar(destino)["orders"] == 2
    assert not (tmp_path / "pizza.duckdb").exists()
    with duckdb.connect(str(destino), read_only=True) as con:
        assert con.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='raw' ORDER BY 1"
        ).fetchall() == [(n,) for n in sorted(FONTES)]


def test_recusa_troca_com_camadas_derivadas_existentes(tmp_path, monkeypatch):
    preparar(tmp_path, monkeypatch)
    with duckdb.connect(str(tmp_path / "pizza.duckdb")) as con:
        con.execute("CREATE SCHEMA refined")
        con.execute("CREATE TABLE refined.orders AS SELECT 7 AS x")
    with pytest.raises(ValueError, match="refined/marts"):
        ingestao.executar()
    with duckdb.connect(str(tmp_path / "pizza.duckdb"), read_only=True) as con:
        assert con.execute("SELECT * FROM refined.orders").fetchall() == [(7,)]


def test_erro_real_de_pagina_parquet_restaura_schema_antigo(tmp_path, monkeypatch):
    pasta = preparar(tmp_path, monkeypatch)
    with duckdb.connect(str(tmp_path / "pizza.duckdb")) as con:
        con.execute("CREATE SCHEMA raw")
        con.execute("CREATE TABLE raw.orders AS SELECT 'anterior' AS id")
        con.execute("CREATE TABLE raw.order_details AS SELECT 7 AS legado")
    # Preserva footer/schema e corrompe páginas: preflight passa, CTAS falha.
    arquivo = pasta / "order_items.parquet"
    dados = bytearray(arquivo.read_bytes())
    inicio_footer = len(dados) - 8 - int.from_bytes(dados[-8:-4], "little")
    dados[4:inicio_footer] = b"\x00" * (inicio_footer - 4)
    arquivo.write_bytes(dados)
    with pytest.raises(ValueError, match="Gravação raw.order_items"):
        ingestao.executar()
    with duckdb.connect(str(tmp_path / "pizza.duckdb"), read_only=True) as con:
        assert con.execute("SELECT * FROM raw.orders").fetchall() == [("anterior",)]
        assert con.execute("SELECT * FROM raw.order_details").fetchall() == [(7,)]
        assert con.execute(
            "SELECT count(*) FROM information_schema.tables WHERE table_schema='raw'"
        ).fetchone() == (2,)


def test_cli_retorna_sucesso(tmp_path, monkeypatch):
    preparar(tmp_path, monkeypatch)
    assert ingestao.main() == 0
