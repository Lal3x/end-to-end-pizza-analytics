"""Valida SELECTs candidatos sem publicar refined; specs/transformacao.md.

Somente SELECTs e configuração de sessão em conexão read_only. Relatório JSON
inclui queries de diagnóstico, hashes dos SELECTs e prova de banco inalterado.
"""

import hashlib
import json
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parents[1]
ARQUIVOS = {
    "orders": "01_orders.sql",
    "order_items": "02_order_items.sql",
    "products": "03_products.sql",
    "customers": "04_customers.sql",
    "stores": "05_stores.sql",
}


def validar() -> dict:
    """Executa propostas sobre RAW e falha em qualquer critério divergente."""
    banco = RAIZ / "pizza.duckdb"
    checksum = hashlib.sha256(banco.read_bytes()).hexdigest()
    consultas = {
        nome: (RAIZ / "sql" / "transformacao" / arquivo).read_text().strip().rstrip(";")
        for nome, arquivo in ARQUIVOS.items()
    }
    relatorio = {"tabelas": {}, "verificacoes": [], "sql_sha256": {}}
    with duckdb.connect(str(banco), read_only=True) as con:
        con.execute("SET TimeZone='UTC'")
        antes = con.execute("SHOW ALL TABLES").fetchall()

        def conferir(nome, sql):
            erros = con.execute(sql).fetchone()[0]
            relatorio["verificacoes"].append({"nome": nome, "erros": erros, "sql": sql})
            if erros:
                raise ValueError(f"{nome}: {erros} falhas")

        for nome in consultas:
            raw = f"raw.{nome}"
            chave = "SKU" if nome == "products" else "id"
            colunas = [r[0] for r in con.execute(f"DESCRIBE {raw}").fetchall()]
            if nome != "order_items":
                conferir(
                    f"{nome}: conflitos de PK",
                    (
                        f'SELECT count(*) FROM (SELECT "{chave}" FROM '
                        f'(SELECT DISTINCT * FROM {raw}) GROUP BY "{chave}" '
                        "HAVING count(*) > 1)"
                    ),
                )
            for coluna in colunas:
                if coluna == "Ingredients":
                    continue
                conferir(
                    f"{nome}.{coluna}: obrigatório",
                    (
                        f'SELECT count(*) FROM {raw} WHERE "{coluna}" IS NULL '
                        f"OR trim(CAST(\"{coluna}\" AS VARCHAR)) = ''"
                    ),
                )

        conferir(
            "orders.total: precisão e domínio",
            (RAIZ / "sql/diagnostico/total_invalido.sql").read_text(),
        )
        conferir(
            "orders.nItems: positivo",
            "SELECT count(*) FROM raw.orders WHERE nItems <= 0",
        )
        conferir(
            "products.Price: formato e domínio",
            (RAIZ / "sql/diagnostico/preco_invalido.sql").read_text(),
        )
        conferir(
            "products: domínios conhecidos",
            """
            SELECT count(*) FROM raw.products
            WHERE Size NOT IN ('Small','Medium','Large','Extra Large')
               OR Category NOT IN ('Classic','Specialty','Vegetarian')
        """,
        )
        conferir(
            "products.Name: categoria consistente",
            """
            SELECT count(*) FROM (SELECT Name FROM raw.products GROUP BY Name
            HAVING count(DISTINCT Category) != 1)
        """,
        )
        for nome in ("customers", "stores"):
            conferir(
                f"{nome}: coordenadas",
                f"""
                SELECT count(*) FROM raw.{nome}
                WHERE try_cast(latitude AS DOUBLE) IS NULL
                   OR try_cast(longitude AS DOUBLE) IS NULL
                   OR NOT isfinite(try_cast(latitude AS DOUBLE))
                   OR NOT isfinite(try_cast(longitude AS DOUBLE))
                   OR try_cast(latitude AS DOUBLE) NOT BETWEEN -90 AND 90
                   OR try_cast(longitude AS DOUBLE) NOT BETWEEN -180 AND 180
            """,
            )
        conferir(
            "stores.distance: conversão finita",
            """
            SELECT count(*) FROM raw.stores WHERE try_cast(distance AS DOUBLE) IS NULL
            OR NOT isfinite(try_cast(distance AS DOUBLE))
        """,
        )

        for nome, sql in consultas.items():
            esquema = con.execute(f"DESCRIBE ({sql})").fetchall()
            campos = [r[0] for r in esquema]
            agregacoes = ["count(*)"] + [
                f'count(*) FILTER (WHERE "{c}" IS NULL)' for c in campos
            ]
            medidas = con.execute(
                f"SELECT {', '.join(agregacoes)} FROM ({sql})"
            ).fetchone()
            raw_colunas = [r[0] for r in con.execute(f"DESCRIBE raw.{nome}").fetchall()]
            nulos_raw = con.execute(
                "SELECT "
                + ", ".join(
                    f'count(*) FILTER (WHERE "{c}" IS NULL)' for c in raw_colunas
                )
                + f" FROM raw.{nome}"
            ).fetchone()
            linhas_raw = con.execute(f"SELECT count(*) FROM raw.{nome}").fetchone()[0]
            distintas = con.execute(
                f"SELECT count(*) FROM (SELECT DISTINCT * FROM raw.{nome})"
            ).fetchone()[0]
            esperado = linhas_raw if nome == "order_items" else distintas
            if medidas[0] != esperado:
                raise ValueError(f"{nome}: contagem alterada fora do contrato")
            nulos_depois = dict(zip(campos, medidas[1:], strict=True))
            for c, n in zip(raw_colunas, nulos_raw, strict=True):
                if nulos_depois[c] != n:
                    raise ValueError(f"{nome}.{c}: nulo fabricado ou removido")
            relatorio["tabelas"][nome] = {
                "linhas_antes": linhas_raw,
                "linhas_depois": medidas[0],
                "repeticoes_exatas_antes": linhas_raw - distintas,
                "nulos_antes": dict(zip(raw_colunas, nulos_raw, strict=True)),
                "nulos_depois": nulos_depois,
                "tipos_depois": {r[0]: r[1] for r in esquema},
            }
            arquivo = RAIZ / "sql" / "transformacao" / ARQUIVOS[nome]
            relatorio["sql_sha256"][ARQUIVOS[nome]] = hashlib.sha256(
                arquivo.read_bytes()
            ).hexdigest()

        for filha, fk, pai, pk in (
            ("orders", "customerId", "customers", "id"),
            ("orders", "storeId", "stores", "id"),
            ("order_items", "orderID", "orders", "id"),
            ("order_items", "SKU", "products", "SKU"),
        ):
            conferir(
                f"FK {filha}.{fk}->{pai}.{pk}",
                (
                    f"SELECT count(*) FROM ({consultas[filha]}) f "
                    f"ANTI JOIN ({consultas[pai]}) p ON f.{fk}=p.{pk}"
                ),
            )
        ctes = (
            f"WITH o AS ({consultas['orders']}), i AS ({consultas['order_items']}), "
            f"p AS ({consultas['products']}), valores AS ("
            "SELECT i.orderID, count(*) AS unidades, sum(p.Price) AS receita "
            "FROM i JOIN p ON i.SKU=p.SKU GROUP BY i.orderID) "
        )
        conferir(
            "Reconciliação por pedido: unidades e centavos",
            ctes
            + """
            SELECT count(*) FROM o LEFT JOIN valores v ON o.id=v.orderID
            WHERE o.nItems IS DISTINCT FROM v.unidades
               OR o.total IS DISTINCT FROM v.receita
        """,
        )
        sql_orders = consultas["orders"]
        conferir(
            "Precisão temporal e nulos intencionais",
            f"""
            SELECT count(*) FROM ({sql_orders})
            WHERE order_date IS NULL
               OR (timestamp_precision='date' AND order_timestamp IS NOT NULL)
               OR (timestamp_precision!='date' AND order_timestamp IS NULL)
        """,
        )
        relatorio["precisao_temporal"] = con.execute(
            f"SELECT timestamp_precision,count(*) FROM ({sql_orders}) "
            "GROUP BY 1 ORDER BY 1"
        ).fetchall()
        relatorio["exemplos_temporais"] = con.execute(
            f"SELECT id,orderDate,CAST(order_date AS VARCHAR),"
            f"CAST(order_timestamp AS VARCHAR),timestamp_precision FROM ({sql_orders}) "
            "QUALIFY row_number() OVER "
            "(PARTITION BY timestamp_precision ORDER BY id)=1 "
            "ORDER BY timestamp_precision"
        ).fetchall()
        relatorio["correcoes_launch"] = con.execute(
            f"SELECT r.SKU,r.Launch,CAST(p.Launch AS VARCHAR) FROM raw.products r "
            f"JOIN ({consultas['products']}) p ON r.SKU=p.SKU "
            "WHERE r.Launch != CAST(p.Launch AS VARCHAR) ORDER BY r.SKU"
        ).fetchall()
        relatorio["maior_desvio_double_centavos"] = con.execute(
            "SELECT max(abs(total-CAST(CAST(total AS DECIMAL(18,2)) AS DOUBLE))) "
            "FROM raw.orders"
        ).fetchone()[0]
        if con.execute("SHOW ALL TABLES").fetchall() != antes:
            raise ValueError("Catálogo alterado")
        relatorio["catalogo_inalterado"] = True
        relatorio["tabelas_existentes"] = [(r[1], r[2]) for r in antes]
    if hashlib.sha256(banco.read_bytes()).hexdigest() != checksum:
        raise ValueError("Bytes do banco alterados")
    relatorio["banco_sha256_antes_depois"] = checksum
    return relatorio


if __name__ == "__main__":
    print(json.dumps(validar(), ensure_ascii=False, indent=2))
