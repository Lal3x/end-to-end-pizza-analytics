"""Provas dos SELECTs candidatos; não implementa/publica a transformação."""

from decimal import Decimal
from pathlib import Path

import duckdb
import pytest

PASTA_SQL = Path(__file__).resolve().parents[1] / "sql" / "transformacao"


def consulta(nome):
    return (PASTA_SQL / nome).read_text().strip().rstrip(";")


def test_orders_preserva_precisao_e_nao_inventa_hora(tmp_path):
    with duckdb.connect(str(tmp_path / "teste.duckdb")) as con:
        con.execute("SET TimeZone='UTC'")
        con.execute("CREATE SCHEMA raw")
        con.execute("""
            CREATE TABLE raw.orders AS SELECT * FROM (VALUES
              (1,'C1','S1','2022-01-01T12:34:56Z',1,1.25::DOUBLE),
              (2,'C1','S1','2022-01-02T12:34Z',1,2.50::DOUBLE),
              (3,'C2','S1','2022-01-03',1,3.75::DOUBLE)
            ) AS t(id,customerId,storeId,orderDate,nItems,total)
        """)
        # Segundos explícitos, minutos explícitos e ausência de hora são distintos.
        sql = consulta("01_orders.sql")
        assert con.execute(
            "SELECT id,CAST(order_date AS VARCHAR),CAST(order_timestamp AS VARCHAR),"
            f"timestamp_precision,total FROM ({sql}) ORDER BY id"
        ).fetchall() == [
            ("1", "2022-01-01", "2022-01-01 12:34:56+00", "second", Decimal("1.25")),
            ("2", "2022-01-02", "2022-01-02 12:34:00+00", "minute", Decimal("2.50")),
            ("3", "2022-01-03", None, "date", Decimal("3.75")),
        ]
        assert con.execute(
            f"SELECT orderDate FROM ({sql}) WHERE id='3'"
        ).fetchone() == ("2022-01-03",)
        assert con.execute(
            "SELECT count(*) FROM information_schema.tables"
        ).fetchone() == (1,)


@pytest.mark.parametrize(
    "data", ["01/01/2022", "2022-02-30T12:00:00Z", "2022-01-01T12:60Z"]
)
def test_orders_formato_ou_data_invalida_nao_vira_nulo(tmp_path, data):
    with duckdb.connect(str(tmp_path / "teste.duckdb")) as con:
        con.execute("CREATE SCHEMA raw")
        con.execute("""
            CREATE TABLE raw.orders (id INTEGER,customerId VARCHAR,storeId VARCHAR,
            orderDate VARCHAR,nItems INTEGER,total DOUBLE)
        """)
        con.execute("INSERT INTO raw.orders VALUES (1,'C1','S1',?,1,1.25)", [data])
        with pytest.raises(duckdb.Error):
            con.execute(consulta("01_orders.sql")).fetchall()
        assert con.execute("SELECT orderDate FROM raw.orders").fetchone() == (data,)


def test_order_items_preserva_unidades_identicas_e_converte_id(tmp_path):
    with duckdb.connect(str(tmp_path / "teste.duckdb")) as con:
        con.execute("CREATE SCHEMA raw")
        con.execute("""
            CREATE TABLE raw.order_items AS SELECT * FROM (VALUES
            ('P01',0),('P01',0),('P02',1)) AS t(SKU,orderID)
        """)
        sql = consulta("02_order_items.sql")
        assert con.execute(f"SELECT * FROM ({sql}) ORDER BY orderID").fetchall() == [
            ("P01", "0"),
            ("P01", "0"),
            ("P02", "1"),
        ]


def test_products_corrige_so_virgula_terminal_e_preserva_raw(tmp_path):
    with duckdb.connect(str(tmp_path / "teste.duckdb")) as con:
        con.execute("CREATE SCHEMA raw")
        con.execute("""
            CREATE TABLE raw.products AS SELECT * FROM (VALUES
            ('P01','Pizza','12.50','Classic','Small',NULL,'2020-01-01,'),
            ('P01','Pizza','12.50','Classic','Small',NULL,'2020-01-01,')
            ) AS t(SKU,Name,Price,Category,Size,Ingredients,Launch)
        """)
        sql = consulta("03_products.sql")
        assert con.execute(
            f"SELECT SKU,Price,Ingredients,CAST(Launch AS VARCHAR) FROM ({sql})"
        ).fetchall() == [("P01", Decimal("12.50"), None, "2020-01-01")]
        assert con.execute("SELECT Launch FROM raw.products").fetchall() == [
            ("2020-01-01,",),
            ("2020-01-01,",),
        ]
        con.execute("UPDATE raw.products SET Launch='2020-01-01,,'")
        with pytest.raises(duckdb.Error):
            con.execute(sql).fetchall()


def test_customers_e_stores_conservam_identificadores_e_medidas(tmp_path):
    with duckdb.connect(str(tmp_path / "teste.duckdb")) as con:
        con.execute("CREATE SCHEMA raw")
        con.execute("""
            CREATE TABLE raw.customers AS SELECT '001' AS id,
            '-23.5' AS latitude,'-46.25' AS longitude
        """)
        con.execute("""
            CREATE TABLE raw.stores AS SELECT 'S01' AS id,'00123' AS zipcode,
            'CA' AS state_abbr,'35.5' AS latitude,'-120.5' AS longitude,
            'Cidade' AS city,'California' AS state,'1.25' AS distance
        """)
        assert con.execute(consulta("04_customers.sql")).fetchone() == (
            "001",
            -23.5,
            -46.25,
        )
        assert con.execute(consulta("05_stores.sql")).fetchone() == (
            "S01",
            "00123",
            "CA",
            35.5,
            -120.5,
            "Cidade",
            "California",
            1.25,
        )


def test_diagnostico_total_aceita_ruido_binario_e_rejeita_fracao_real(tmp_path):
    sql = (PASTA_SQL.parent / "diagnostico/total_invalido.sql").read_text()
    with duckdb.connect(str(tmp_path / "teste.duckdb")) as con:
        con.execute("CREATE SCHEMA raw")
        con.execute("CREATE TABLE raw.orders(total DOUBLE)")
        # Duas entradas válidas; as seis restantes devem impedir publicação.
        valores = [
            1.25,
            1.2500000000000002,
            1.251,
            None,
            float("nan"),
            float("inf"),
            -1.0,
            1e20,
        ]
        con.executemany("INSERT INTO raw.orders VALUES (?)", [(v,) for v in valores])
        assert con.execute(sql).fetchone() == (6,)


def test_diagnostico_preco_nao_arredonda_texto_com_terceira_casa(tmp_path):
    sql = (PASTA_SQL.parent / "diagnostico/preco_invalido.sql").read_text()
    with duckdb.connect(str(tmp_path / "teste.duckdb")) as con:
        con.execute("CREATE SCHEMA raw")
        con.execute("CREATE TABLE raw.products(Price VARCHAR)")
        # Três preços válidos; demais formatos não podem virar preço corrigido.
        valores = ["12.50", "0", "12.5", "12.501", "NaN", "-1", "1,00", "", None]
        con.executemany("INSERT INTO raw.products VALUES (?)", [(v,) for v in valores])
        assert con.execute(sql).fetchone() == (6,)
