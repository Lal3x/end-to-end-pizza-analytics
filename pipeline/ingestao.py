"""Espelho Pizza Paradise em RAW, conforme specs/ingestao.md.

CSV textual por pandas e Parquet tipado por DuckDB, sem deduplicar ocorrências.
Todas as fontes são pré-validadas antes de abrir o destino. A transação recria
somente RAW e falhas preservam a versão anterior; logs só após commit.
"""

import argparse
import csv
import sys
from pathlib import Path

import duckdb
import pandas as pd

import db

FONTES = {
    "orders": {
        "arquivo": "orders.parquet",
        "colunas": ["id", "customerId", "storeId", "orderDate", "nItems", "total"],
        "tipos": ["INTEGER", "VARCHAR", "VARCHAR", "VARCHAR", "INTEGER", "DOUBLE"],
    },
    "order_items": {
        "arquivo": "order_items.parquet",
        "colunas": ["SKU", "orderID"],
        "tipos": ["VARCHAR", "INTEGER"],
    },
    "customers": {
        "arquivo": "customers.csv",
        "colunas": ["id", "latitude", "longitude"],
    },
    "stores": {
        "arquivo": "stores.csv",
        "colunas": [
            "id",
            "zipcode",
            "state_abbr",
            "latitude",
            "longitude",
            "city",
            "state",
            "distance",
        ],
    },
    "products": {
        "arquivo": "products.csv",
        "colunas": [
            "SKU",
            "Name",
            "Price",
            "Category",
            "Size",
            "Ingredients",
            "Launch",
        ],
    },
}


def validar_fontes() -> dict[str, pd.DataFrame]:
    """Pré-valida as cinco fontes sem abrir destino; retorna os três CSVs textuais.

    Compartilhada com executar_pipeline.py conforme specs/execucao-pipeline.md.
    Falhas identificam caminho e causa; não modifica nenhum arquivo de origem.
    """
    pasta = db.PASTA_RAW / "pizza_paradise"
    faltantes = [
        fonte["arquivo"]
        for fonte in FONTES.values()
        if not (pasta / fonte["arquivo"]).is_file()
    ]
    if faltantes:
        raise ValueError(f"Fontes ausentes em {pasta}: {', '.join(faltantes)}")

    quadros = {}
    with duckdb.connect(":memory:") as validador:
        for nome, fonte in FONTES.items():
            caminho = pasta / fonte["arquivo"]
            try:
                if caminho.suffix == ".parquet":
                    esquema = validador.execute(
                        "DESCRIBE SELECT * FROM read_parquet(?)", [str(caminho)]
                    ).fetchall()
                    if [r[0] for r in esquema] != fonte["colunas"]:
                        raise ValueError("Colunas Parquet divergentes")
                    if [r[1] for r in esquema] != fonte["tipos"]:
                        raise ValueError("Tipos Parquet divergentes")
                else:
                    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
                        leitor = csv.reader(arquivo, strict=True)
                        if next(leitor, None) != fonte["colunas"]:
                            raise ValueError(f"Cabeçalho esperado: {fonte['colunas']}")
                        for numero, campos in enumerate(leitor, start=2):
                            if len(campos) != len(fonte["colunas"]):
                                raise ValueError(f"Registro {numero}: campos inválidos")
                    quadros[nome] = pd.read_csv(
                        caminho,
                        encoding="utf-8-sig",
                        dtype="string",
                        keep_default_na=False,
                        na_values=[""],
                        skip_blank_lines=False,
                    )
            except (ValueError, OSError, csv.Error, duckdb.Error) as erro:
                raise ValueError(f"Fonte {caminho}: {erro}") from erro
    return quadros


def executar(
    banco: Path | None = None, *, con: duckdb.DuckDBPyConnection | None = None
) -> dict[str, int]:
    """Publica RAW conforme specs/ingestao.md e specs/execucao-pipeline.md.

    Args:
        banco: Destino opcional, exclusivo de con; padrão pizza.duckdb na raiz.
        con: Conexão externa com transação ativa controlada pelo chamador.

    Returns:
        Contagens do banco. Com con externo, ainda dependem do commit do chamador.

    Raises:
        ValueError: Se fontes divergirem, argumentos conflitarem ou houver
            refined/marts existentes. A proteção da ingestão isolada permanece.
        duckdb.Error: Se abertura/gravação/transação falhar.

    Sem con, abre/fecha conexão e controla a transação; com con, apenas executa
    as regras da etapa e propaga falhas. Não confirma nem fecha conexão externa.
    """
    if banco is not None and con is not None:
        raise ValueError("Use banco ou con, nunca ambos")
    propria = con is None
    quadros = validar_fontes()
    pasta = db.PASTA_RAW / "pizza_paradise"

    if propria and banco is not None:
        banco = Path(banco)
        banco.parent.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect(str(banco))
    elif propria:
        con = db.conectar()
    try:
        if con.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema IN ('refined', 'marts')"
        ).fetchone()[0]:
            raise ValueError(
                "refined/marts existentes: revisar migração antes de trocar RAW"
            )
        if propria:
            con.execute("BEGIN")
        try:
            con.execute("DROP SCHEMA IF EXISTS raw CASCADE")
            db.criar_schema(con, "raw")
            contagens = {}
            for nome, fonte in FONTES.items():
                try:
                    if fonte["arquivo"].endswith(".parquet"):
                        con.execute(
                            f'CREATE TABLE raw."{nome}" AS '
                            "SELECT * FROM read_parquet(?)",
                            [str(pasta / fonte["arquivo"])],
                        )
                        contagens[nome] = con.execute(
                            f'SELECT count(*) FROM raw."{nome}"'
                        ).fetchone()[0]
                    else:
                        contagens[nome] = db.gravar(con, quadros[nome], "raw", nome)
                except duckdb.Error as erro:
                    raise ValueError(f"Gravação raw.{nome}: {erro}") from erro
            if propria:
                con.execute("COMMIT")
        except Exception:
            if propria:
                con.execute("ROLLBACK")
            raise
    finally:
        if propria:
            con.close()
    return contagens


def main() -> int:
    """CLI: diagnóstico em stderr e contagens apenas após transação publicada."""
    parser = argparse.ArgumentParser(description="Ingestão Pizza Paradise")
    parser.add_argument("--banco", type=Path, help="Banco separado para ensaio")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        contagens = executar(args.banco)
    except Exception as erro:
        print(f"Erro na ingestão: {erro}", file=sys.stderr)
        return 1
    for nome, quantidade in contagens.items():
        print(f"raw.{nome:<16} {quantidade:,} linhas".replace(",", "."))
    print(f"total {sum(contagens.values()):,} linhas".replace(",", "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
