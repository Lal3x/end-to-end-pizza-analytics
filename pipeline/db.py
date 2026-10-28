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

PASTA_RAW = Path(__file__).resolve().parents[1] / "raw"


def conectar() -> duckdb.DuckDBPyConnection:
    """Abre pizza.duckdb na raiz do projeto; o chamador deve fechar."""
    return duckdb.connect(str(PASTA_RAW.parent / "pizza.duckdb"))


def criar_schema(con: duckdb.DuckDBPyConnection, nome: str) -> None:
    """Cria o schema sem interpretar seu identificador como código SQL."""
    identificador = '"' + nome.replace('"', '""') + '"'
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {identificador}")


def gravar(
    con: duckdb.DuckDBPyConnection,
    df: pd.DataFrame,
    schema: str,
    tabela: str,
) -> int:
    """Substitui tabela sem transformar o DataFrame ou confirmar a transação."""
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
