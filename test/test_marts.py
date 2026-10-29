"""Contrato specs/marts.md: fontes sintéticas e DuckDB temporário real."""

import shutil
from decimal import Decimal

import duckdb
import pytest

from pipeline import marts


@pytest.fixture
def banco(tmp_path):
    """Quatro pedidos e cinco ocorrências; receita 100, produto A com 80%."""
    caminho = tmp_path / "teste.duckdb"
    with duckdb.connect(str(caminho)) as con:
        con.execute("""
            CREATE SCHEMA refined;
            CREATE TABLE refined.orders (
                id VARCHAR, customerId VARCHAR, storeId VARCHAR, nItems INTEGER,
                total DECIMAL(18,2), order_date DATE,
                order_timestamp TIMESTAMPTZ, timestamp_precision VARCHAR
            );
            INSERT INTO refined.orders VALUES
                ('1','c1','s1',2,40,'2020-01-02','2020-01-02 00:00:00+00','second'),
                ('2','c1','s1',1,40,'2021-01-02','2021-01-02 12:30:00+00','minute'),
                ('3','c2','s2',1,10,'2021-02-02','2021-02-02 12:30:20+00','second'),
                ('4','c3','s2',1,10,'2021-02-03',NULL,'date');
            CREATE TABLE refined.products (
                SKU VARCHAR, Name VARCHAR, Size VARCHAR,
                Category VARCHAR, Price DECIMAL(18,2)
            );
            INSERT INTO refined.products VALUES
                ('a1','A','Small','Classic',20), ('a2','A','Large','Classic',40),
                ('b1','B','Small','Classic',10), ('c1','C','Small','Classic',10);
            CREATE TABLE refined.order_items (orderID VARCHAR, SKU VARCHAR);
            INSERT INTO refined.order_items VALUES
                ('1','a1'), ('1','a1'), ('2','a2'), ('3','b1'), ('4','c1');
            CREATE TABLE refined.customers (id VARCHAR);
            INSERT INTO refined.customers VALUES ('c1'),('c2'),('c3'),('sem compra');
            CREATE TABLE refined.stores (id VARCHAR, city VARCHAR, state VARCHAR);
            INSERT INTO refined.stores VALUES
                ('s1','Cidade 1','Estado'),('s2','Cidade 2','Estado'),
                ('sem venda','Outra','Estado');
        """)
    return caminho


@pytest.fixture
def pasta(tmp_path):
    """Isola o inventário para testar arquivos com erro sem alterar o projeto."""
    destino = tmp_path / "sql"
    shutil.copytree(marts.PASTA_SQL / "marts", destino)
    return destino


def test_indicadores_e_reexecucao(banco):
    for _ in range(2):
        resultado = marts.executar(banco)
        assert len(resultado["tabelas"]) == 13
        with duckdb.connect(str(banco)) as con:
            assert con.sql(
                "SELECT pedidos,unidades,receita,ticket_medio FROM marts.kpis"
            ).fetchone() == (
                4,
                5,
                Decimal("100.00"),
                25.0,
            )
            assert con.sql("SELECT count(*) FROM marts.vendas_mensais").fetchone() == (
                3,
            )
            assert con.sql(
                "SELECT SKU,posicao FROM marts.ranking_pizzas ORDER BY SKU"
            ).fetchall() == [
                ("a1", 1),
                ("a2", 1),
                ("b1", 2),
                ("c1", 2),
            ]
            assert con.sql(
                "SELECT Name,receita FROM marts.ranking_tipos_pizza ORDER BY Name"
            ).fetchall() == [
                ("A", Decimal("80.00")),
                ("B", Decimal("10.00")),
                ("C", Decimal("10.00")),
            ]
            assert con.sql(
                "SELECT unidades FROM marts.quantidade_por_pedido WHERE orderID='1'"
            ).fetchone() == (2,)
            assert con.sql(
                "SELECT hora_local,hora_nao_informada,pedidos "
                "FROM marts.pedidos_hora ORDER BY hora_local NULLS LAST"
            ).fetchall() == [
                (9, False, 2),
                (21, False, 1),
                (None, True, 1),
            ]
            assert con.sql(
                "SELECT Name FROM marts.concentracao_pizzas "
                "WHERE grupo_80 ORDER BY ordem"
            ).fetchall() == [("A",)]
            assert con.sql(
                "SELECT frequencia,clientes,proporcao_recompra "
                "FROM marts.frequencia_clientes ORDER BY frequencia"
            ).fetchall() == [
                (1, 2, pytest.approx(1 / 3)),
                (2, 1, pytest.approx(1 / 3)),
            ]
            assert con.sql("SELECT count(*) FROM marts.vendas_loja").fetchone() == (2,)
            con.execute("CREATE TABLE marts.obsoleto AS SELECT 1 AS x")
    with duckdb.connect(str(banco)) as con:
        con.execute("DROP TABLE marts.obsoleto")
        assert con.sql("SELECT count(*) FROM refined.order_items").fetchone() == (5,)


def test_pareto_inclui_produto_que_cruza_e_desempata_por_nome(banco):
    with duckdb.connect(str(banco)) as con:
        con.execute("UPDATE refined.products SET Price=30 WHERE SKU='a2'")
        con.execute("UPDATE refined.orders SET total=30 WHERE id='2'")
    marts.executar(banco)
    with duckdb.connect(str(banco)) as con:
        assert con.sql(
            "SELECT Name,grupo_80,produtos_80 "
            "FROM marts.concentracao_pizzas ORDER BY ordem"
        ).fetchall() == [
            ("A", True, 2),
            ("B", True, 2),
            ("C", False, 2),
        ]


def test_clientes_sem_recompra_tem_proporcao_zero(banco):
    with duckdb.connect(str(banco)) as con:
        con.execute("UPDATE refined.orders SET customerId='sem compra' WHERE id='2'")
    marts.executar(banco)
    with duckdb.connect(str(banco)) as con:
        assert con.sql(
            "SELECT proporcao_recompra FROM marts.frequencia_clientes"
        ).fetchall() == [(0.0,)]


@pytest.mark.parametrize(
    "alteracao", ["ausente", "prefixo", "duplicado", "extra", "vazia"]
)
def test_inventario_invalido_preserva_marts(banco, pasta, alteracao):
    marts.executar(banco)
    arquivo = pasta / "01_vendas_mensais.sql"
    if alteracao == "ausente":
        arquivo.unlink()
    elif alteracao == "prefixo":
        arquivo.rename(pasta / "x_vendas_mensais.sql")
    elif alteracao == "duplicado":
        (pasta / "01_extra.sql").write_text("SELECT 1")
    elif alteracao == "extra":
        (pasta / "README.md").write_text("inesperado")
    else:
        for sql in pasta.iterdir():
            sql.unlink()
    with pytest.raises(ValueError, match="Inventário"):
        marts.executar(banco, pasta)
    with duckdb.connect(str(banco)) as con:
        assert con.sql("SELECT receita FROM marts.kpis").fetchone() == (Decimal("100"),)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT FROM",
        "SELECT * FROM raw.orders",
        "SELECT * FROM marts.kpis",
        "SELECT * FROM refined.orders; DROP SCHEMA refined CASCADE",
        "SELECT * FROM refined.orders WHERE false",
        "SELECT coluna_inexistente FROM refined.orders",
        "SELECT mes, pedidos, unidades, receita+1 AS receita FROM "
        "(SELECT date_trunc('month',order_date)::DATE AS mes, count(*) AS pedidos, "
        "sum(nItems) AS unidades, sum(total) AS receita "
        "FROM refined.orders GROUP BY 1)",
    ],
)
def test_sql_invalido_vazio_ou_inconsistente_restaura_marts(banco, pasta, sql):
    marts.executar(banco)
    (pasta / "01_vendas_mensais.sql").write_text(sql, encoding="utf-8")
    with pytest.raises(ValueError):
        marts.executar(banco, pasta)
    with duckdb.connect(str(banco)) as con:
        assert con.sql("SELECT receita FROM marts.kpis").fetchone() == (Decimal("100"),)
        assert con.sql("SELECT sum(receita) FROM marts.vendas_mensais").fetchone() == (
            Decimal("100"),
        )


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE refined.orders SET total=0; UPDATE refined.products SET Price=0",
        "UPDATE refined.orders SET customerId='orfao' WHERE id='1'",
        "INSERT INTO refined.orders SELECT * FROM refined.orders LIMIT 1",
        "UPDATE refined.orders SET total=41 WHERE id='1'",
        "UPDATE refined.orders SET timestamp_precision='date' WHERE id='1'",
        "UPDATE refined.products SET Category='Outra' WHERE SKU='a2'",
        "DELETE FROM refined.order_items",
        "ALTER TABLE refined.orders ALTER total TYPE DOUBLE",
    ],
)
def test_refined_invalida_bloqueia_publicacao(banco, sql):
    marts.executar(banco)
    with duckdb.connect(str(banco)) as con:
        con.execute(sql)
    with pytest.raises(ValueError):
        marts.executar(banco)
    with duckdb.connect(str(banco)) as con:
        assert con.sql("SELECT receita FROM marts.kpis").fetchone() == (Decimal("100"),)


def test_banco_ausente_nao_cria_arquivo(tmp_path):
    caminho = tmp_path / "ausente.duckdb"
    with pytest.raises(ValueError, match="Banco ausente"):
        marts.executar(caminho)
    assert not caminho.exists()


def test_nome_do_arquivo_igual_ao_schema(banco, tmp_path):
    destino = tmp_path / "marts.duckdb"
    shutil.copyfile(banco, destino)
    marts.executar(destino)
    with duckdb.connect(str(destino)) as con:
        assert con.sql('SELECT receita FROM "marts".marts.kpis').fetchone() == (
            Decimal("100"),
        )


def test_horas_sao_paulo_independem_da_sessao_e_preservam_data_fonte(banco):
    marts.executar(banco)
    sql = (marts.PASTA_SQL / "marts/04_pedidos_hora.sql").read_text()
    with duckdb.connect(str(banco)) as con:
        for fuso in ("UTC", "Asia/Tokyo"):
            con.execute(f"SET TimeZone='{fuso}'")
            assert (
                con.execute(
                    (marts.PASTA_SQL / "validar_refined.sql").read_text()
                ).fetchall()
                == []
            )
            assert con.execute(sql).fetchall() == [
                (9, "America/Sao_Paulo", False, 2),
                (21, "America/Sao_Paulo", False, 1),
                (None, "America/Sao_Paulo", True, 1),
            ]
        # O pedido de 00h UTC passa a 21h na véspera, sem mudar o calendário
        # original nos marts mensal/dia da semana nem inventar hora para NULL.
        assert (
            str(
                con.sql(
                    "SELECT order_date FROM refined.orders WHERE id='1'"
                ).fetchone()[0]
            )
            == "2020-01-02"
        )
