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

from pipeline import db
from pipeline.fontes import FONTES


def executar(banco: Path | None = None) -> dict[str, int]:
    """Substitui RAW atomicamente; destino opcional permite carga de ensaio."""
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

    if banco is not None:
        banco = Path(banco)
        banco.parent.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect(str(banco))
    else:
        con = db.conectar()
    try:
        if con.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema IN ('refined', 'marts')"
        ).fetchone()[0]:
            raise ValueError(
                "refined/marts existentes: revisar migração antes de trocar RAW"
            )
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
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
    finally:
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
