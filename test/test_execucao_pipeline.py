"""Transação global conforme specs/execucao-pipeline.md; fontes sintéticas reais."""

import csv
import json
import shutil
from collections import Counter
from decimal import Decimal

import duckdb
import pytest

import db
import executar_pipeline as completo
from pipeline import ingestao, marts, transformacao


@pytest.fixture
def fontes(tmp_path, monkeypatch):
    """Dois pedidos, um sem hora, e três ocorrências do mesmo produto."""
    raiz = tmp_path / "raw"
    pasta = raiz / "pizza_paradise"
    pasta.mkdir(parents=True)
    monkeypatch.setattr(db, "PASTA_RAW", raiz)
    monkeypatch.setattr(completo, "RAIZ", tmp_path)
    linhas = {
        "customers": [["C1", "-23", "-46"]],
        "stores": [["S1", "00123", "CA", "35", "-120", "Cidade", "Estado", "1"]],
        "products": [
            ["PZ026", "Pizza", "10.00", "Classic", "Small", "queijo", "2020-01-01,"]
        ],
    }
    for nome, registros in linhas.items():
        with (pasta / f"{nome}.csv").open("w", encoding="utf-8", newline="") as arquivo:
            escritor = csv.writer(arquivo)
            escritor.writerow(ingestao.FONTES[nome]["colunas"])
            escritor.writerows(registros)
    with duckdb.connect(":memory:") as con:
        con.execute(
            "COPY (SELECT id, 'C1' AS customerId, 'S1' AS storeId, orderDate, "
            "nItems, total::DOUBLE AS total FROM (VALUES "
            "(1,'2020-01-01T00:30Z',2,20),(2,'2021-01-01',1,10)) "
            "v(id,orderDate,nItems,total)) TO ? (FORMAT PARQUET)",
            [str(pasta / "orders.parquet")],
        )
        con.execute(
            "COPY (SELECT 'PZ026' AS SKU, orderID FROM (VALUES (1),(1),(2)) "
            "v(orderID)) TO ? (FORMAT PARQUET)",
            [str(pasta / "order_items.parquet")],
        )
    return pasta


def retrato(banco):
    """Compara conteúdo, multiplicidades, tipos e schemas, sem números da base real."""
    with duckdb.connect(str(banco), read_only=True) as con:
        con.execute("SET TimeZone='UTC'")
        tabelas = con.execute(
            "SELECT table_schema,table_name FROM information_schema.tables "
            "WHERE table_schema IN ('raw','refined','marts','pessoal') ORDER BY 1,2"
        ).fetchall()
        return {
            (schema, nome): (
                con.execute(f"DESCRIBE {schema}.{nome}").fetchall(),
                # Serialização nativa preserva valores sem depender do adaptador
                # opcional pytz para fetchall de TIMESTAMPTZ no Python.
                Counter(
                    con.execute(f"SELECT to_json(t) FROM {schema}.{nome} t").fetchall()
                ),
            )
            for schema, nome in tabelas
        }


def alterar_produto(pasta, *, invalido=False):
    """Altera a fonte para detectar rollback que preserve só parte da carga."""
    arquivo = pasta / "products.csv"
    with arquivo.open(encoding="utf-8", newline="") as origem:
        linhas = list(csv.reader(origem))
    linhas[1][1] = "Produto alterado"
    if invalido:
        linhas[1][2] = "10.001"
    with arquivo.open("w", encoding="utf-8", newline="") as destino:
        csv.writer(destino).writerows(linhas)


def test_execucao_reexecucao_e_preservacao_de_outro_schema(fontes, tmp_path):
    banco = tmp_path / "pizza.duckdb"
    with duckdb.connect(str(banco)) as con:
        con.execute("CREATE SCHEMA pessoal")
        con.execute("CREATE TABLE pessoal.notas AS SELECT 'notebook' AS texto")
    resultado = completo.executar_pipeline()
    assert resultado["estado"] == "publicado"
    assert list(resultado["etapas"]) == ["ingestao", "transformacao", "marts"]
    assert resultado["etapas"]["ingestao"]["order_items"] == 3
    with duckdb.connect(str(banco), read_only=True) as con:
        assert con.sql(
            "SELECT pedidos,unidades,receita FROM marts.kpis"
        ).fetchone() == (
            2,
            3,
            Decimal("30.00"),
        )
        assert con.sql("SELECT texto FROM pessoal.notas").fetchone() == ("notebook",)
    antes = retrato(banco)
    completo.executar_pipeline(banco)
    assert retrato(banco) == antes
    assert len([t for t in antes if t[0] == "raw"]) == 5
    assert len([t for t in antes if t[0] == "refined"]) == 5
    assert len([t for t in antes if t[0] == "marts"]) == 13


@pytest.mark.parametrize("existente", [False, True])
def test_pre_validacao_nao_cria_ou_modifica_banco(fontes, tmp_path, existente):
    banco = tmp_path / "teste.duckdb"
    if existente:
        completo.executar_pipeline(banco)
        antes = retrato(banco)
    (fontes / "stores.csv").unlink()
    with pytest.raises(RuntimeError, match="pré-validação.*stores.csv"):
        completo.executar_pipeline(banco)
    if existente:
        assert retrato(banco) == antes
    else:
        assert not banco.exists()


@pytest.mark.parametrize("existente", [False, True])
def test_conversao_invalida_reverte_ate_raw(fontes, tmp_path, existente):
    banco = tmp_path / "teste.duckdb"
    if existente:
        completo.executar_pipeline(banco)
        antes = retrato(banco)
    alterar_produto(fontes, invalido=True)
    with pytest.raises(RuntimeError, match="transformacao.*products.Price"):
        completo.executar_pipeline(banco)
    if existente:
        assert retrato(banco) == antes
    else:
        assert not banco.exists()
        assert not banco.with_suffix(".duckdb.wal").exists()


def test_falha_sql_reverte_todas_as_camadas(fontes, tmp_path, monkeypatch):
    banco = tmp_path / "teste.duckdb"
    completo.executar_pipeline(banco)
    with duckdb.connect(str(banco)) as con:
        con.execute("CREATE SCHEMA pessoal")
        con.execute("CREATE TABLE pessoal.notas AS SELECT 7 AS valor")
    antes = retrato(banco)
    alterar_produto(fontes)
    pasta = tmp_path / "sql"
    shutil.copytree(marts.PASTA_SQL, pasta)
    (pasta / "marts/10_kpis.sql").write_text(
        "SELECT inexistente FROM refined.orders", encoding="utf-8"
    )
    monkeypatch.setattr(marts, "PASTA_SQL", pasta)
    with pytest.raises(RuntimeError, match="marts"):
        completo.executar_pipeline(banco)
    assert retrato(banco) == antes


@pytest.mark.parametrize("modulo", [ingestao, transformacao, marts])
def test_etapa_nao_confirma_nem_fecha_conexao_externa(fontes, tmp_path, modulo):
    banco = tmp_path / "teste.duckdb"
    ingestao.executar(banco)
    if modulo is marts:
        transformacao.executar(banco)
    antes = retrato(banco)
    with duckdb.connect(str(banco)) as con:
        con.execute("BEGIN")
        modulo.executar(con=con)
        assert con.sql("SELECT 1").fetchone() == (1,)
        con.execute("ROLLBACK")
    assert retrato(banco) == antes


@pytest.mark.parametrize("modulo", [ingestao, transformacao, marts])
def test_argumentos_conflitantes_nao_escrevem(fontes, tmp_path, modulo):
    banco = tmp_path / "nao-criar.duckdb"
    with duckdb.connect(":memory:") as con:
        with pytest.raises(ValueError, match="nunca ambos"):
            modulo.executar(banco=banco, con=con)
        assert con.sql("SELECT 1").fetchone() == (1,)
    assert not banco.exists()


def test_ingestao_isolada_continua_bloqueando_derivadas(fontes, tmp_path):
    banco = tmp_path / "teste.duckdb"
    completo.executar_pipeline(banco)
    antes = retrato(banco)
    with pytest.raises(ValueError, match="refined/marts existentes"):
        ingestao.executar(banco)
    assert retrato(banco) == antes


def test_cli_sucesso_e_falha_sem_saida_parcial(fontes, tmp_path, monkeypatch, capsys):
    banco = tmp_path / "teste.duckdb"
    monkeypatch.setattr("sys.argv", ["executar_pipeline", "--banco", str(banco)])
    assert completo.main() == 0
    assert json.loads(capsys.readouterr().out)["estado"] == "publicado"
    alterar_produto(fontes, invalido=True)
    assert completo.main() == 1
    saida = capsys.readouterr()
    assert saida.out == ""
    assert "transformacao" in saida.err


def test_interrupcao_reverte_e_retorna_130(fontes, tmp_path, monkeypatch, capsys):
    banco = tmp_path / "teste.duckdb"
    completo.executar_pipeline(banco)
    antes = retrato(banco)

    def interromper(**kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(transformacao, "executar", interromper)
    monkeypatch.setattr("sys.argv", ["executar_pipeline", "--banco", str(banco)])
    assert completo.main() == 130
    assert "interrompido" in capsys.readouterr().err
    assert retrato(banco) == antes
