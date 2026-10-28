"""Auditoria independente de RAW; contrato em specs/ingestao.md.

Compara multiconjuntos com EXCEPT ALL, não apenas contagens ou hashes de linhas.
Somente leitura; não transforma nem publica camadas.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import duckdb


def main() -> None:
    """Falha em diferenças de valor, multiplicidade, tipo, coluna ou relação."""
    from pipeline import db
    from pipeline.fontes import FONTES

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--banco", type=Path, default=db.PASTA_RAW.parent / "pizza.duckdb"
    )
    args = parser.parse_args()
    relatorio = {"tabelas": {}, "orfãos": {}, "banco": str(args.banco)}
    with duckdb.connect(str(args.banco), read_only=True) as con:
        for nome, fonte in FONTES.items():
            caminho = db.PASTA_RAW / "pizza_paradise" / fonte["arquivo"]
            if hashlib.sha256(caminho.read_bytes()).hexdigest() != fonte["sha256"]:
                raise ValueError(f"Hash divergente: {caminho}")
            origem = (
                "read_parquet(?)"
                if caminho.suffix == ".parquet"
                else "read_csv(?, header=true, all_varchar=true, nullstr='')"
            )
            divergencias = []
            for esquerda, direita in ((f"raw.{nome}", origem), (origem, f"raw.{nome}")):
                divergencias.append(
                    con.execute(
                        f"SELECT count(*) FROM (SELECT * FROM {esquerda} "
                        f"EXCEPT ALL SELECT * FROM {direita})",
                        [str(caminho)],
                    ).fetchone()[0]
                )
            if any(divergencias):
                raise ValueError(f"Valores/multiplicidades divergentes: {nome}")
            esquema = con.execute(f"DESCRIBE raw.{nome}").fetchall()
            if [r[0] for r in esquema] != fonte["colunas"]:
                raise ValueError(f"Colunas divergentes: {nome}")
            tipos = fonte.get("tipos", ["VARCHAR"] * len(fonte["colunas"]))
            if [r[1] for r in esquema] != tipos:
                raise ValueError(f"Tipos divergentes: {nome}")
            relatorio["tabelas"][nome] = {
                "linhas": con.execute(f"SELECT count(*) FROM raw.{nome}").fetchone()[0],
                "diferencas_except_all": divergencias,
                "tipos": dict(zip(fonte["colunas"], tipos, strict=True)),
                "sha256_fonte": fonte["sha256"],
            }
        tabelas = con.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='raw' ORDER BY 1"
        ).fetchall()
        if [r[0] for r in tabelas] != sorted(FONTES):
            raise ValueError("Tabelas RAW ausentes ou de fonte anterior")
        for filha, fk, pai, pk in (
            ("orders", "customerId", "customers", "id"),
            ("orders", "storeId", "stores", "id"),
            ("order_items", "orderID", "orders", "id"),
            ("order_items", "SKU", "products", "SKU"),
        ):
            quantidade = con.execute(
                f"SELECT count(*) FROM raw.{filha} f ANTI JOIN raw.{pai} p "
                f"ON f.{fk}=p.{pk}"
            ).fetchone()[0]
            relatorio["orfãos"][f"{filha}.{fk}->{pai}.{pk}"] = quantidade
            if quantidade:
                raise ValueError(f"Órfãos: {filha}.{fk}")
        relatorio["repeticoes_itens_alem_da_primeira"] = con.execute(
            "SELECT (SELECT count(*) FROM raw.order_items) - "
            "(SELECT count(*) FROM (SELECT DISTINCT * FROM raw.order_items))"
        ).fetchone()[0]
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    main()
