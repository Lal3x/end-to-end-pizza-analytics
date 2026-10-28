"""Provas sintéticas do contrato specs/db.md, sem banco ou CSV do projeto."""

import importlib.util
from decimal import Decimal
from pathlib import Path

import duckdb
import pandas as pd
import pytest

from pipeline import db


def test_importar_modulo_nao_cria_banco(tmp_path):
    # Executar o módulo com localização isolada detecta efeitos na importação.
    origem = Path(db.__file__)
    modulo_local = tmp_path / "pipeline" / "db.py"
    modulo_local.parent.mkdir()
    modulo_local.write_bytes(origem.read_bytes())
    spec = importlib.util.spec_from_file_location("db_isolado", modulo_local)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)

    assert modulo.PASTA_RAW == tmp_path / "raw"
    assert not (tmp_path / "pizza.duckdb").exists()


def test_conectar_independe_da_pasta_corrente_e_fechar_libera_banco(
    tmp_path, monkeypatch
):
    # A raiz de teste e o diretório de execução são distintos.
    raiz = tmp_path / "projeto"
    raiz.mkdir()
    outra = tmp_path / "outra"
    outra.mkdir()
    monkeypatch.setattr(db, "PASTA_RAW", raiz / "raw")
    monkeypatch.chdir(outra)
    con = db.conectar()
    try:
        con.execute("CREATE TABLE exemplo AS SELECT 1 AS valor")
    finally:
        con.close()

    assert (raiz / "pizza.duckdb").exists()
    assert not (outra / "pizza.duckdb").exists()
    with duckdb.connect(str(raiz / "pizza.duckdb"), read_only=True) as leitura:
        assert leitura.execute("SELECT valor FROM exemplo").fetchone() == (1,)


def test_gravar_preserva_texto_nulo_inteiro_e_decimal_e_nao_duplica(tmp_path):
    # Três linhas provam zero inicial, nulo verdadeiro e centavos exatos.
    dados = pd.DataFrame(
        {
            "codigo": pd.Series(["001", None, "003"], dtype="string"),
            "quantidade": pd.Series([2, 1, 3], dtype="int32"),
            "preco": [Decimal("1.25"), Decimal("2.50"), Decimal("0.00")],
        }
    )
    with duckdb.connect(str(tmp_path / "teste.duckdb")) as con:
        db.criar_schema(con, "raw")
        db.criar_schema(con, "raw")
        assert db.gravar(con, dados, "raw", "exemplo") == 3
        assert db.gravar(con, dados, "raw", "exemplo") == 3
        assert con.execute(
            "SELECT * FROM raw.exemplo ORDER BY quantidade"
        ).fetchall() == [
            (None, 1, Decimal("2.50")),
            ("001", 2, Decimal("1.25")),
            ("003", 3, Decimal("0.00")),
        ]
        tipos = con.execute("DESCRIBE raw.exemplo").fetchall()
        assert [(r[0], r[1]) for r in tipos] == [
            ("codigo", "VARCHAR"),
            ("quantidade", "INTEGER"),
            ("preco", "DECIMAL(3,2)"),
        ]
        assert con.execute(
            "SELECT count(*) FROM duckdb_views() "
            "WHERE starts_with(view_name, '_pizza_frame_')"
        ).fetchone() == (0,)


def test_gravar_substitui_valores_em_vez_de_acrescentar(tmp_path):
    with duckdb.connect(str(tmp_path / "teste.duckdb")) as con:
        db.criar_schema(con, "raw")
        assert db.gravar(con, pd.DataFrame({"x": [1, 2]}), "raw", "exemplo") == 2
        assert db.gravar(con, pd.DataFrame({"x": [9]}), "raw", "exemplo") == 1
        assert con.execute("SELECT * FROM raw.exemplo").fetchall() == [(9,)]


def test_rollback_restaura_tabela_anterior_sem_commit_implicito(tmp_path):
    with duckdb.connect(str(tmp_path / "teste.duckdb")) as con:
        db.criar_schema(con, "raw")
        db.gravar(con, pd.DataFrame({"x": [7]}), "raw", "exemplo")
        con.execute("BEGIN")
        db.gravar(con, pd.DataFrame({"x": [8, 9]}), "raw", "exemplo")
        assert con.execute("SELECT count(*) FROM raw.exemplo").fetchone() == (2,)
        con.execute("ROLLBACK")
        assert con.execute("SELECT * FROM raw.exemplo").fetchall() == [(7,)]


def test_falha_propaga_erro_e_remove_registro_temporario(tmp_path):
    # Schema ausente provoca falha real do DuckDB, sem mock.
    with duckdb.connect(str(tmp_path / "teste.duckdb")) as con:
        with pytest.raises(duckdb.CatalogException, match="inexistente"):
            db.gravar(con, pd.DataFrame({"x": [1]}), "inexistente", "exemplo")
        assert con.execute(
            "SELECT count(*) FROM duckdb_views() "
            "WHERE starts_with(view_name, '_pizza_frame_')"
        ).fetchone() == (0,)
        assert con.execute("SELECT 1").fetchone() == (1,)


def test_nomes_com_aspas_sao_identificadores_e_nao_comandos(tmp_path):
    with duckdb.connect(str(tmp_path / "teste.duckdb")) as con:
        db.criar_schema(con, 'camada"especial')
        assert (
            db.gravar(con, pd.DataFrame({"x": [1]}), 'camada"especial', 'nome"especial')
            == 1
        )
        assert con.execute(
            'SELECT x FROM "camada""especial"."nome""especial"'
        ).fetchone() == (1,)
