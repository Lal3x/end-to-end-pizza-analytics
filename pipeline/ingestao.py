"""Espelho dos CSVs em raw, conforme specs/ingestao.md, regras 1–7.

Valida todas as fontes antes de abrir o banco, mantém campos textuais e nulos,
sem limpeza ou deduplicação. A transação única evita cargas parciais; contagens
do banco só são anunciadas após commit. Importar não executa a ingestão.
"""

import csv
import sys

import pandas as pd

from pipeline import db

FONTES = {
    "orders": ("utf-8-sig", ["order_id", "date", "time"]),
    "order_details": (
        "utf-8-sig",
        ["order_details_id", "order_id", "pizza_id", "quantity"],
    ),
    "pizzas": ("utf-8-sig", ["pizza_id", "pizza_type_id", "size", "price"]),
    "pizza_types": ("cp1252", ["pizza_type_id", "name", "category", "ingredients"]),
}


def executar() -> dict[str, int]:
    """Valida fontes, substitui raw atomicamente e retorna contagens gravadas."""
    faltantes = [
        f"{nome}.csv" for nome in FONTES if not (db.PASTA_RAW / f"{nome}.csv").is_file()
    ]
    if faltantes:
        raise ValueError(f"Fontes ausentes em {db.PASTA_RAW}: {', '.join(faltantes)}")

    quadros = {}
    for nome, (encoding, colunas) in FONTES.items():
        caminho = db.PASTA_RAW / f"{nome}.csv"
        try:
            with caminho.open(encoding=encoding, newline="") as arquivo:
                leitor = csv.reader(arquivo, strict=True)
                if next(leitor, None) != colunas:
                    raise ValueError(f"Cabeçalho esperado: {colunas}")
                for registro, campos in enumerate(leitor, start=2):
                    if len(campos) != len(colunas):
                        raise ValueError(
                            f"Registro {registro}: número de campos inválido"
                        )
            quadros[nome] = pd.read_csv(
                caminho,
                encoding=encoding,
                dtype="string",
                keep_default_na=False,
                na_values=[""],
                skip_blank_lines=False,
            )
        except (ValueError, OSError, csv.Error) as erro:
            raise ValueError(f"Fonte {caminho}: {erro}") from erro

    con = db.conectar()
    try:
        con.execute("BEGIN")
        try:
            db.criar_schema(con, "raw")
            contagens = {}
            for nome, quadro in quadros.items():
                contagens[nome] = db.gravar(con, quadro, "raw", nome)
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
    finally:
        con.close()
    return contagens


def main() -> int:
    """Interface CLI: erro claro em stderr, sucesso somente após commit."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        contagens = executar()
    except Exception as erro:
        print(f"Erro na ingestão: {erro}", file=sys.stderr)
        return 1
    for nome, quantidade in contagens.items():
        print(f"raw.{nome:<16} {quantidade:,} linhas".replace(",", "."))
    print(f"total {sum(contagens.values()):,} linhas".replace(",", "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
