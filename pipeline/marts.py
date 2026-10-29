"""Executa os 13 marts conforme specs/marts.md; fórmulas e auditorias em SQL.

Valida inventário e refined antes do DROP. Publica todas as tabelas em uma
transação; qualquer falha restaura marts anteriores. Não altera RAW/refined.
"""

import argparse
import json
import re
import sys
import time
from contextlib import nullcontext
from pathlib import Path

import duckdb

import db

PASTA_SQL = Path(__file__).resolve().parents[1] / "sql"
NOMES = (
    "vendas_mensais",
    "ranking_pizzas",
    "pedidos_dia_semana",
    "pedidos_hora",
    "ticket_por_pedido",
    "receita_categoria",
    "vendas_tamanho",
    "concentracao_pizzas",
    "quantidade_por_pedido",
    "kpis",
    "ranking_tipos_pizza",
    "vendas_loja",
    "frequencia_clientes",
)
FONTES = {"orders", "order_items", "products", "customers", "stores"}


def ler_sqls(pasta: Path, con: duckdb.DuckDBPyConnection) -> list[tuple[str, str]]:
    """Lê o inventário exato e aceita um SELECT por arquivo, somente de refined.

    Raises:
        ValueError: Se faltarem arquivos ou houver nomes, fontes ou SQL inválidos.
    """
    esperados = [f"{i:02}_{nome}.sql" for i, nome in enumerate(NOMES, 1)]
    encontrados = sorted(p.name for p in pasta.iterdir()) if pasta.is_dir() else []
    if encontrados != esperados:
        raise ValueError(
            f"Inventário de marts inválido: esperado {esperados}; "
            f"encontrado {encontrados}"
        )
    consultas = []
    for arquivo in esperados:
        sql = (
            (pasta / arquivo)
            .read_text(encoding="utf-8")
            .strip()
            .removesuffix(";")
            .rstrip()
        )
        try:
            instrucoes = con.extract_statements(sql)
            if (
                len(instrucoes) != 1
                or instrucoes[0].type != duckdb.StatementType.SELECT
            ):
                raise ValueError("esperado um SELECT")
            fontes = {
                fonte.split(" AS ", 1)[0]
                for fonte in con.get_table_names(sql, qualified=True)
            }
            if not fontes or not fontes <= {f"refined.{nome}" for nome in FONTES}:
                raise ValueError(f"fontes fora de refined: {fontes}")
        except (duckdb.Error, ValueError) as erro:
            raise ValueError(f"{arquivo}: {erro}") from erro
        consultas.append((re.sub(r"^\d+_", "", arquivo[:-4]), sql))
    return consultas


def auditar(con: duckdb.DuckDBPyConnection, arquivo: str) -> None:
    """Executa SQL de validação; linhas retornadas identificam violações."""
    falhas = con.execute((PASTA_SQL / arquivo).read_text(encoding="utf-8")).fetchall()
    if falhas:
        raise ValueError(f"{arquivo}: {[linha[0] for linha in falhas]}")


def executar(
    banco: Path | None = None,
    pasta: Path | None = None,
    *,
    con: duckdb.DuckDBPyConnection | None = None,
) -> dict:
    """Publica marts atomicamente e retorna contagens somente após commit.

    Args:
        banco: Banco existente; padrão pizza.duckdb na raiz.
        pasta: Diretório dos 13 SELECTs; padrão sql/marts.
        con: Conexão externa com transação ativa; exclusiva de banco. Conforme
            specs/execucao-pipeline.md, o chamador confirma/reverte e fecha.

    Raises:
        ValueError: Se inventário, fontes, grãos ou reconciliações divergirem.
        duckdb.Error: Se leitura, execução SQL ou transação falhar.

    Fecha a conexão em qualquer resultado e preserva a versão anterior em erro.
    """
    caminho = Path(banco) if banco is not None else db.PASTA_RAW.parent / "pizza.duckdb"
    if banco is not None and con is not None:
        raise ValueError("Use banco ou con, nunca ambos")
    propria = con is None
    if propria and not caminho.is_file():
        raise ValueError(f"Banco ausente: {caminho}")
    inicio = time.perf_counter()
    # Alias fixo evita ambiguidade entre catálogo e schema se o arquivo se
    # chamar marts.duckdb ou refined.duckdb. O banco em memória não recebe dados.
    with duckdb.connect(":memory:") if propria else nullcontext(con) as con:
        if propria:
            literal = str(caminho.resolve()).replace("'", "''")
            con.execute(f"ATTACH '{literal}' AS destino")
            con.execute("USE destino")
        con.execute("SET TimeZone='UTC'")
        consultas = ler_sqls(
            Path(pasta) if pasta is not None else PASTA_SQL / "marts", con
        )
        if propria:
            con.execute("BEGIN")
        try:
            for nome in FONTES:
                if not con.execute(f"SELECT count(*) FROM refined.{nome}").fetchone()[
                    0
                ]:
                    raise ValueError(f"refined.{nome}: tabela vazia")
            for tabela, coluna in (("orders", "total"), ("products", "Price")):
                tipos = {
                    r[0]: r[1]
                    for r in con.execute(f"DESCRIBE refined.{tabela}").fetchall()
                }
                if tipos.get(coluna) != "DECIMAL(18,2)":
                    raise ValueError(
                        f"refined.{tabela}.{coluna}: esperado DECIMAL(18,2)"
                    )
            auditar(con, "validar_refined.sql")
            con.execute("DROP SCHEMA IF EXISTS marts CASCADE")
            db.criar_schema(con, "marts")
            contagens = {}
            for nome, sql in consultas:
                try:
                    con.execute(f'CREATE TABLE marts."{nome}" AS {sql}')
                    contagens[nome] = con.execute(
                        f'SELECT count(*) FROM marts."{nome}"'
                    ).fetchone()[0]
                    if not contagens[nome]:
                        raise ValueError("mart obrigatório vazio")
                except (duckdb.Error, ValueError) as erro:
                    raise ValueError(f"marts.{nome}: {erro}") from erro
            auditar(con, "validar_marts.sql")
            if propria:
                con.execute("COMMIT")
        except Exception:
            if propria:
                con.execute("ROLLBACK")
            raise
    return {"tabelas": contagens, "segundos": round(time.perf_counter() - inicio, 3)}


def main() -> int:
    """CLI UTF-8; imprime somente publicação concluída ou diagnóstico de erro."""
    parser = argparse.ArgumentParser(description="Marts SQL Pizza Paradise")
    parser.add_argument("--banco", type=Path, help="Banco existente para ensaio")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        print(json.dumps(executar(args.banco), ensure_ascii=False, indent=2))
    except Exception as erro:
        print(f"Erro nos marts: {erro}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
