"""Contrato de ingestão com CSVs inventados e DuckDB real em tmp_path."""

import csv

import duckdb
import pytest

from pipeline import db, ingestao


def preparar(tmp_path, monkeypatch):
    """Escreve fontes mínimas; nunca acessa os CSVs reais."""
    pasta = tmp_path / "raw"
    pasta.mkdir()
    monkeypatch.setattr(db, "PASTA_RAW", pasta)
    linhas = {
        # Duplicata intencional e valores não convertidos na RAW.
        "orders": [["001", "31/12/2015", "09:00:00"]] * 2,
        "order_details": [["01", "001", "teste_m", "02"]],
        "pizzas": [["teste_m", "teste", "M", "12.50"]],
        # Acento cp1252, lista com vírgula e quebra de linha entre aspas.
        "pizza_types": [["teste", "Ação", "NA", "tomate, queijo\n fresco"]],
    }
    for nome, (encoding, colunas) in ingestao.FONTES.items():
        with (pasta / f"{nome}.csv").open("w", encoding=encoding, newline="") as f:
            escritor = csv.writer(f)
            escritor.writerow(colunas)
            escritor.writerows(linhas[nome])
    return pasta


def test_preserva_valores_duplicatas_tipos_e_reexecucao(tmp_path, monkeypatch):
    preparar(tmp_path, monkeypatch)
    esperado = {"orders": 2, "order_details": 1, "pizzas": 1, "pizza_types": 1}
    assert ingestao.executar() == esperado
    assert ingestao.executar() == esperado
    with duckdb.connect(str(tmp_path / "pizza.duckdb"), read_only=True) as con:
        assert (
            con.execute("SELECT * FROM raw.orders").fetchall()
            == [("001", "31/12/2015", "09:00:00")] * 2
        )
        assert con.execute("SELECT * FROM raw.pizza_types").fetchone() == (
            "teste",
            "Ação",
            "NA",
            "tomate, queijo\n fresco",
        )
        assert con.execute("SELECT quantity FROM raw.order_details").fetchone() == (
            "02",
        )
        assert con.execute("SELECT price FROM raw.pizzas").fetchone() == ("12.50",)
        assert con.execute(
            "SELECT DISTINCT data_type FROM information_schema.columns "
            "WHERE table_schema='raw'"
        ).fetchall() == [("VARCHAR",)]


def test_nulo_inteiramente_vazio_continua_varchar_e_tokens_sao_texto(
    tmp_path, monkeypatch
):
    pasta = preparar(tmp_path, monkeypatch)
    (pasta / "pizza_types.csv").write_text(
        "pizza_type_id,name,category,ingredients\n"
        "teste,NA,NULL,\nsegundo,N/A,  Classic  ,\n",
        encoding="cp1252",
    )
    assert ingestao.executar()["pizza_types"] == 2
    with duckdb.connect(str(tmp_path / "pizza.duckdb"), read_only=True) as con:
        assert con.execute(
            "SELECT * FROM raw.pizza_types ORDER BY pizza_type_id"
        ).fetchall() == [
            ("segundo", "N/A", "  Classic  ", None),
            ("teste", "NA", "NULL", None),
        ]
        assert con.execute("DESCRIBE raw.pizza_types").fetchall()[-1][1] == "VARCHAR"


def test_fonte_ausente_falha_antes_de_criar_banco(tmp_path, monkeypatch):
    pasta = preparar(tmp_path, monkeypatch)
    (pasta / "orders.csv").unlink()
    with pytest.raises(ValueError, match="orders.csv"):
        ingestao.executar()
    assert ingestao.main() == 1
    assert not (tmp_path / "pizza.duckdb").exists()


@pytest.mark.parametrize(
    "conteudo",
    [
        "errado,date,time\n1,2015-01-01,10:00:00\n",  # Cabeçalho divergente.
        "order_id,date,time\n1,2015-01-01\n",  # Campo ausente.
        "order_id,date,time\n1,2015-01-01,10:00:00,extra\n",  # Campo excedente.
        "order_id,date,time\n\n",  # Linha vazia não pode ser descartada.
        'order_id,date,time\n1,"sem fim',  # Aspas inválidas.
    ],
)
def test_csv_invalido_nao_altera_raw_anterior(tmp_path, monkeypatch, conteudo):
    pasta = preparar(tmp_path, monkeypatch)
    ingestao.executar()
    (pasta / "orders.csv").write_text(conteudo, encoding="utf-8")
    with pytest.raises(ValueError, match="orders.csv"):
        ingestao.executar()
    with duckdb.connect(str(tmp_path / "pizza.duckdb"), read_only=True) as con:
        assert con.execute("SELECT count(*) FROM raw.orders").fetchone() == (2,)


def test_encoding_invalido_falha_sem_criar_banco(tmp_path, monkeypatch):
    pasta = preparar(tmp_path, monkeypatch)
    (pasta / "orders.csv").write_bytes(b"order_id,date,time\n\xff,a,b\n")
    with pytest.raises(ValueError, match="orders.csv"):
        ingestao.executar()
    assert not (tmp_path / "pizza.duckdb").exists()


def test_erro_na_ultima_gravacao_restaura_todas_as_tabelas(tmp_path, monkeypatch):
    preparar(tmp_path, monkeypatch)
    with duckdb.connect(str(tmp_path / "pizza.duckdb")) as con:
        con.execute("CREATE SCHEMA raw")
        con.execute("CREATE TABLE raw.orders AS SELECT 'anterior' AS order_id")
        # View no destino final provoca erro real, após três gravações.
        con.execute("CREATE VIEW raw.pizza_types AS SELECT 9 AS valor")
    with pytest.raises(duckdb.Error):
        ingestao.executar()
    with duckdb.connect(str(tmp_path / "pizza.duckdb"), read_only=True) as con:
        assert con.execute("SELECT * FROM raw.orders").fetchall() == [("anterior",)]
        assert con.execute("SELECT * FROM raw.pizza_types").fetchall() == [(9,)]
        assert con.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema='raw' AND table_name IN ('pizzas', 'order_details')"
        ).fetchone() == (0,)


def test_cli_retorna_sucesso(tmp_path, monkeypatch):
    preparar(tmp_path, monkeypatch)
    assert ingestao.main() == 0
