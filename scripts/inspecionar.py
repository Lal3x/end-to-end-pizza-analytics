"""Inspeção somente leitura do ZIP, conforme specs/etapa-zero.md.

Não ingere nem transforma dados persistidos. Encodings são explícitos: a falha
UTF-8 observada em pizza_types exige cp1252, sem descartar bytes inválidos.
Campo CSV vazio é contado separadamente da interpretação futura como NULL.
"""

import csv
import hashlib
import io
import json
import sys
from collections import Counter
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile

ENCODINGS = {
    "orders": "utf-8-sig",
    "order_details": "utf-8-sig",
    "pizzas": "utf-8-sig",
    "pizza_types": "cp1252",
    "data_dictionary": "utf-8-sig",
}


def inspect(path: Path) -> dict:
    """Mede todas as linhas; não cria banco, corrige ou remove registros."""
    report = {"zip_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    tables = {}
    rows = {}
    with ZipFile(path) as archive:
        report["files"] = archive.namelist()
        for name, encoding in ENCODINGS.items():
            content = archive.read(f"{name}.csv")
            reader = csv.DictReader(io.StringIO(content.decode(encoding)))
            records = list(reader)
            columns = reader.fieldnames
            if not columns or any(
                None in row or None in row.values() for row in records
            ):
                raise ValueError(f"Estrutura CSV inválida: {name}")
            rows[name] = records
            keys = ["Table", "Field"] if name == "data_dictionary" else [columns[0]]
            tables[name] = {
                "sha256": hashlib.sha256(content).hexdigest(),
                "bytes": len(content),
                "encoding": encoding,
                "columns": columns,
                "rows": len(records),
                "empty_fields": {
                    col: sum(row[col] == "" for row in records) for col in columns
                },
                "exact_duplicates": len(records)
                - len({tuple(row.values()) for row in records}),
                "key": keys,
                "repeated_keys": len(records)
                - len({tuple(row[k] for k in keys) for row in records}),
            }
    report["tables"] = tables
    relationships = []
    for child, fk, parent, pk in (
        ("order_details", "order_id", "orders", "order_id"),
        ("order_details", "pizza_id", "pizzas", "pizza_id"),
        ("pizzas", "pizza_type_id", "pizza_types", "pizza_type_id"),
    ):
        parent_keys = {row[pk] for row in rows[parent]}
        child_keys = {row[fk] for row in rows[child]}
        relationships.append(
            {
                "child": child,
                "fk": fk,
                "parent": parent,
                "pk": pk,
                "orphan_rows": sum(row[fk] not in parent_keys for row in rows[child]),
                "parents_without_children": len(parent_keys - child_keys),
            }
        )
    report["relationships"] = relationships
    dates = [
        datetime.strptime(row["date"], "%d/%m/%Y").date() for row in rows["orders"]
    ]
    for row in rows["orders"]:
        datetime.strptime(row["time"], "%H:%M:%S")
    quantities = [int(row["quantity"]) for row in rows["order_details"]]
    prices = [Decimal(row["price"]) for row in rows["pizzas"]]
    order_sizes = Counter(row["order_id"] for row in rows["order_details"])
    pairs = Counter((r["order_id"], r["pizza_id"]) for r in rows["order_details"])
    variants = Counter((r["pizza_type_id"], r["size"]) for r in rows["pizzas"])
    report["profile"] = {
        "date_format": "%d/%m/%Y",
        "time_format": "%H:%M:%S",
        "date_min": str(min(dates)),
        "date_max": str(max(dates)),
        "nonpositive_quantities": sum(q <= 0 for q in quantities),
        "quantity_min": min(quantities),
        "quantity_max": max(quantities),
        "negative_prices": sum(p < 0 for p in prices),
        "price_min": str(min(prices)),
        "price_max": str(max(prices)),
        "prices_with_more_than_two_decimals": sum(
            p.as_tuple().exponent < -2 for p in prices
        ),
        "sizes": sorted({r["size"] for r in rows["pizzas"]}),
        "categories": sorted({r["category"] for r in rows["pizza_types"]}),
        "max_lines_per_order": max(order_sizes.values()),
        "orders_with_multiple_lines": sum(n > 1 for n in order_sizes.values()),
        "repeated_order_pizza_pairs": sum(n - 1 for n in pairs.values()),
        "repeated_type_size_pairs": sum(n - 1 for n in variants.values()),
    }
    return report


if __name__ == "__main__":
    print(json.dumps(inspect(Path(sys.argv[1])), ensure_ascii=False, indent=2))
