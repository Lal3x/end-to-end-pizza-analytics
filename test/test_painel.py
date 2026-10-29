"""Contrato specs/dashboard.md: formatos, leitura e figuras com dados sintéticos."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import duckdb
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

import db
import painel


@pytest.fixture
def dados():
    """Dois pedidos, três unidades e receita 30; Pareto precisa dos dois nomes."""
    return {
        "kpis": pd.DataFrame(
            [
                {
                    "pedidos": 2,
                    "unidades": 3,
                    "receita": Decimal("30.00"),
                    "ticket_medio": 15.0,
                    "unidades_por_pedido": 1.5,
                    "data_inicial": date(2020, 1, 1),
                    "data_final": date(2021, 1, 1),
                }
            ]
        ),
        "vendas_mensais": pd.DataFrame(
            {
                "mes": [date(2020, 1, 1), date(2021, 1, 1)],
                "receita": [Decimal("10.00"), Decimal("20.00")],
                "pedidos": [1, 1],
            }
        ),
        "ranking_tipos_pizza": pd.DataFrame(
            {
                "Name": ["B", "A"],
                "receita": [Decimal("10.00"), Decimal("20.00")],
                "posicao": [2, 1],
            }
        ),
        "ranking_pizzas": pd.DataFrame(
            {
                "SKU": ["B1", "A1"],
                "Name": ["B", "A"],
                "Size": ["Small", "Large"],
                "receita": [Decimal("10.00"), Decimal("20.00")],
                "posicao": [2, 1],
            }
        ),
        "concentracao_pizzas": pd.DataFrame(
            {
                "Name": ["A", "B"],
                "receita": [Decimal("20.00"), Decimal("10.00")],
                "ordem": [1, 2],
                "participacao_acumulada": [2 / 3, 1.0],
                "grupo_80": [True, True],
                "produtos_80": [2, 2],
                "proporcao_produtos_80": [1.0, 1.0],
            }
        ),
        "pedidos_dia_semana": pd.DataFrame({"dia_iso": [3, 5], "pedidos": [1, 1]}),
        "pedidos_hora": pd.DataFrame(
            {
                "hora_local": [21, None],
                "fuso_horario": ["America/Sao_Paulo"] * 2,
                "hora_nao_informada": [False, True],
                "pedidos": [1, 1],
            }
        ),
        "receita_categoria": pd.DataFrame(
            {"Category": ["Classic"], "receita": [Decimal("30.00")]}
        ),
        "vendas_loja": pd.DataFrame(
            {
                "storeId": ["S1"],
                "city": ["Cidade"],
                "state": ["Estado"],
                "receita": [Decimal("30.00")],
            }
        ),
        "frequencia_clientes": pd.DataFrame(
            {"frequencia": [1], "clientes": [2], "proporcao_recompra": [0.0]}
        ),
    }


@pytest.fixture
def banco(tmp_path, dados):
    """DuckDB isolado real; nenhum arquivo do projeto é aberto pelos testes."""
    caminho = tmp_path / "teste.duckdb"
    with duckdb.connect(str(caminho)) as con:
        db.criar_schema(con, "marts")
        for nome, df in dados.items():
            db.gravar(con, df, "marts", nome)
    return caminho


@pytest.mark.parametrize(
    "valor,casas,esperado",
    [
        (1234567, 0, "1.234.567"),
        (Decimal("1003.86"), 2, "1.003,86"),
        (Decimal("9999999999999999.99"), 2, "9.999.999.999.999.999,99"),
        (0, 0, "0"),
        (-15.5, 2, "-15,50"),
    ],
)
def test_numero_sem_locale_ou_perda_de_decimal(valor, casas, esperado):
    assert painel.numero(valor, casas) == esperado


def test_moeda_original_e_percentual_pronto():
    assert painel.valor_monetario(Decimal("10.50")) == "10,50"
    assert painel.pct(Decimal("0.932")) == "93,2%"
    assert painel.pct(0) == "0,0%"
    assert painel.pct(1) == "100,0%"


@pytest.mark.parametrize("valor", [None, "erro", True, float("nan"), float("inf")])
def test_numero_invalido_falha_sem_inventar_zero(valor):
    with pytest.raises(ValueError):
        painel.numero(valor)
    with pytest.raises(ValueError):
        painel.pct(valor)


@pytest.mark.parametrize("casas", [-1, 7, 1.5, True])
def test_precisao_invalida(casas):
    with pytest.raises(ValueError):
        painel.numero(1, casas)


def test_ler_preserva_decimal_e_libera_conexao(banco, dados, monkeypatch, tmp_path):
    monkeypatch.setattr(painel, "BANCO", banco)
    monkeypatch.chdir(tmp_path)
    lidos = painel.ler()
    assert set(lidos) == set(dados)
    assert lidos["kpis"].iloc[0]["receita"] == Decimal("30.00")
    assert isinstance(lidos["kpis"].iloc[0]["receita"], Decimal)
    # Uma escrita real após a leitura prova que não há conexão read_only pendurada.
    with duckdb.connect(str(banco)) as con:
        con.execute("UPDATE marts.kpis SET receita=40")
    assert painel.ler(banco)["kpis"].iloc[0]["receita"] == Decimal("40.00")


def test_banco_ausente_nao_cria_arquivo(tmp_path):
    caminho = tmp_path / "ausente.duckdb"
    with pytest.raises(FileNotFoundError):
        painel.ler(caminho)
    assert not caminho.exists()


def test_erro_lista_fontes_ausentes_vazias_e_colunas(banco):
    with duckdb.connect(str(banco)) as con:
        con.execute("DROP TABLE marts.vendas_loja")
        con.execute("DELETE FROM marts.pedidos_hora")
        con.execute("ALTER TABLE marts.kpis DROP receita")
    with pytest.raises(ValueError) as erro:
        painel.ler(banco)
    assert "vendas_loja: tabela ausente" in str(erro.value)
    assert "pedidos_hora: tabela vazia" in str(erro.value)
    assert "kpis: colunas ausentes ['receita']" in str(erro.value)
    with duckdb.connect(str(banco)) as con:
        assert con.sql("SELECT 1").fetchone() == (1,)


def test_mensal_usa_medidas_originais(dados):
    df = dados["vendas_mensais"]
    receita = painel.vendas_mensais(df)
    pedidos = painel.vendas_mensais(df, "pedidos")
    assert list(receita.data[0].y) == [Decimal("10.00"), Decimal("20.00")]
    assert list(pedidos.data[0].y) == [1, 1]
    assert list(receita.data[0].customdata) == ["10,00", "20,00"]
    with pytest.raises(ValueError):
        painel.vendas_mensais(df, "outra")


def test_ranking_preserva_granularidade_e_ordem(dados):
    fig = painel.ranking(dados["ranking_tipos_pizza"])
    assert list(fig.data[0].y) == ["A", "B"]
    assert list(fig.data[0].x) == [Decimal("20.00"), Decimal("10.00")]
    variantes = painel.ranking(dados["ranking_pizzas"], True)
    assert list(variantes.data[0].y) == ["A1", "B1"]
    assert variantes.layout.yaxis.autorange == "reversed"


def test_pareto_mostra_nomes_e_nao_recalcula_acumulado(dados):
    fig = painel.pareto(dados["concentracao_pizzas"])
    assert list(fig.data[0].x) == ["A", "B"]
    assert list(fig.data[1].y) == [2 / 3, 1.0]
    assert list(fig.data[1].customdata) == ["66,7%", "100,0%"]
    assert fig.layout.shapes[0].y0 == 0.8
    assert fig.layout.xaxis.tickangle == -55
    assert list(fig.layout.yaxis2.tickvals) == [0, 0.2, 0.4, 0.6, 0.8, 1]


def test_hora_desconhecida_nao_vira_meia_noite(dados):
    fig = painel.pedidos_hora(dados["pedidos_hora"])
    assert list(fig.data[0].x) == ["21h"]
    assert list(fig.data[0].y) == [1]
    somente_sem_hora = dados["pedidos_hora"].iloc[[1]]
    vazio = painel.pedidos_hora(somente_sem_hora)
    assert vazio.layout.annotations[0].text == "Nenhum horário informado"


def test_demais_graficos_preservam_medidas(dados):
    assert list(painel.pedidos_semana(dados["pedidos_dia_semana"]).data[0].x) == [
        "Quarta",
        "Sexta",
    ]
    assert list(painel.categorias(dados["receita_categoria"]).data[0].x) == [
        Decimal("30.00")
    ]
    lojas = painel.lojas(dados["vendas_loja"])
    assert list(lojas.data[0].y) == ["S1"]
    assert list(lojas.data[0].customdata[0]) == ["Cidade", "Estado", "30,00"]


def test_app_interacoes_e_recarga_sem_banco_real(banco, monkeypatch):
    monkeypatch.setattr(painel, "BANCO", banco)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"))
    app.run(timeout=20)
    assert not app.exception
    assert len(app.get("plotly_chart")) == 7
    app.radio[0].set_value("Pedidos").run()
    app.radio[1].set_value("Variantes (SKU)").run()
    assert not app.exception
    assert any("02 · Produtos" in item.value for item in app.subheader)
    with duckdb.connect(str(banco)) as con:
        con.execute("UPDATE marts.kpis SET receita=40,ticket_medio=20")
    app.run()
    assert any('class="valor">30,00' in item.value for item in app.markdown)
    app.button[0].click().run()
    assert not app.exception
    assert any('class="valor">40,00' in item.value for item in app.markdown)


def test_app_fonte_ausente_exibe_orientacao(tmp_path, monkeypatch):
    caminho = tmp_path / "nao-existe.duckdb"
    monkeypatch.setattr(painel, "BANCO", caminho)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()
    assert not app.exception
    assert "Banco ausente" in app.error[0].value
    assert "pipeline.marts" in app.code[0].value
    assert not caminho.exists()
