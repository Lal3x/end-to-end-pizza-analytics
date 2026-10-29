"""Acesso comum ao DuckDB, conforme specs/db.md (D1–D4).

Resolve caminhos pelo módulo, sem abrir banco na importação. As etapas decidem
colunas e tipos e controlam transações; este módulo não transforma dados nem
faz commit. O chamador sempre fecha a conexão. Registros de DataFrames são
removidos mesmo em erro para não deixar recursos temporários na conexão.
"""

from pathlib import Path
from uuid import uuid4

import duckdb
import pandas as pd

PASTA_RAW = Path(__file__).resolve().parent / "raw"


def conectar() -> duckdb.DuckDBPyConnection:
    """Abre o banco local definido em specs/db.md.

    Returns:
        Conexão com pizza.duckdb na raiz do projeto. O chamador deve fechá-la
        e controlar suas transações.

    Raises:
        duckdb.Error: Se o arquivo não puder ser aberto, inclusive por bloqueio.
    """
    return duckdb.connect(str(PASTA_RAW.parent / "pizza.duckdb"))


def criar_schema(con: duckdb.DuckDBPyConnection, nome: str) -> None:
    """Cria um schema, escapando seu nome como identificador SQL.

    Args:
        con: Conexão aberta, cuja transação pertence ao chamador.
        nome: Nome literal do schema a criar, caso ainda não exista.

    Raises:
        duckdb.Error: Se a criação falhar. Não confirma a transação.
    """
    identificador = '"' + nome.replace('"', '""') + '"'
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {identificador}")


def gravar(
    con: duckdb.DuckDBPyConnection,
    df: pd.DataFrame,
    schema: str,
    tabela: str,
) -> int:
    """Substitui uma tabela pelo DataFrame, conforme specs/db.md.

    Args:
        con: Conexão aberta, cuja transação pertence ao chamador.
        df: Dados já preparados pela etapa responsável.
        schema: Nome literal de um schema existente.
        tabela: Nome literal da tabela de destino.

    Returns:
        Quantidade de linhas consultada na tabela após a gravação.

    Raises:
        duckdb.Error: Se o registro ou a gravação falhar. Não executa commit;
            remove o registro temporário mesmo quando a gravação falha.
    """
    schema_sql = '"' + schema.replace('"', '""') + '"'
    tabela_sql = '"' + tabela.replace('"', '""') + '"'
    destino = f"{schema_sql}.{tabela_sql}"
    registro = f"_pizza_frame_{uuid4().hex}"
    con.register(registro, df)
    try:
        con.execute(f'CREATE OR REPLACE TABLE {destino} AS SELECT * FROM "{registro}"')
        return con.execute(f"SELECT count(*) FROM {destino}").fetchone()[0]
    finally:
        con.unregister(registro)
