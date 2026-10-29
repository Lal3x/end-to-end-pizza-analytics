"""Interface Streamlit conforme specs/dashboard.md e design/rascunho.png.

Só organiza o que painel.py lê, formata e desenha. Cache contém DataFrames,
nunca conexões. As interações selecionam série/ranking sem recalcular KPIs.
"""

from html import escape
from pathlib import Path

import duckdb
import streamlit as st

import painel


@st.cache_data(show_spinner="Lendo os marts…")
def carregar(banco: str) -> dict:
    """Guarda somente dados; painel.ler fecha o DuckDB em cada leitura."""
    return painel.ler(Path(banco))


def cartao(titulo: str, valor: str, definicao: str, origem: str) -> None:
    """Renderiza texto escapado, sem calcular a medida exibida."""
    st.markdown(
        '<div class="cartao"><div class="rotulo">'
        + escape(titulo)
        + '</div><div class="valor">'
        + escape(valor)
        + '</div><div class="definicao">'
        + escape(definicao)
        + '</div><div class="origem">'
        + escape(origem)
        + "</div></div>",
        unsafe_allow_html=True,
    )


def grafico(figura, chave: str) -> None:
    """Exibe figura já construída, sem cálculos de negócio na interface."""
    st.plotly_chart(
        figura, width="stretch", theme=None, key=chave, config={"displaylogo": False}
    )


def main() -> None:
    """Monta as faixas do desenho e interrompe claramente se os marts faltarem."""
    st.set_page_config(
        page_title="Pizza Paradise · Visão executiva", page_icon="◈", layout="wide"
    )
    st.markdown(
        """
        <style>
        .stMainBlockContainer{max-width:1600px;padding-top:2rem}
        h3{font-size:1.25rem!important;line-height:1.4!important}
        [data-testid="stSidebar"]{background:#083e50}
        [data-testid="stSidebar"] h1,[data-testid="stSidebar"] p,
        [data-testid="stSidebar"] a{color:#d8f5fa}
        [data-testid="stSidebar"] button{background:#155a6e;color:#fff}
        .cartao{background:#fff;border:1px solid #dcecef;border-top:3px solid #0891b2;
          border-radius:14px;padding:20px;height:100%;min-height:155px}
        .rotulo{font-size:13px;color:#526e7a;font-weight:600}
        .valor{font-size:clamp(22px,2vw,32px);font-weight:750;letter-spacing:-1px;
          margin:8px 0;color:#164e63;overflow-wrap:anywhere}
        .definicao{font-size:11px;color:#526e7a}
        .origem{font-size:10px;color:#427583;margin-top:7px;overflow-wrap:anywhere}
        [class*="st-key-caixa_"]{background:white;border-radius:14px;padding:18px}
        a:focus-visible,button:focus-visible{outline:3px solid #eab308!important}
        </style>
    """,
        unsafe_allow_html=True,
    )
    with st.sidebar:
        st.title("Pizza Paradise")
        st.caption("INTELIGÊNCIA DE VENDAS")
        st.markdown(
            "[Visão executiva](#visao-executiva)\n\n[Produtos](#produtos)\n\n"
            "[Demanda e lojas](#demanda-e-lojas)\n\n[Sobre os dados](#sobre-os-dados)"
        )
        if st.button("Recarregar dados", width="stretch"):
            carregar.clear()
        st.caption(
            "Dados fictícios · Observable\n\n"
            "Após atualizar os marts, recarregue o painel."
        )
    try:
        dados = carregar(str(painel.BANCO))
    except (FileNotFoundError, ValueError, duckdb.Error) as erro:
        st.error(f"Não foi possível ler os indicadores: {erro}")
        st.code("uv run python -m pipeline.marts", language="bash")
        st.stop()

    k = dados["kpis"].iloc[0]
    p = dados["concentracao_pizzas"].sort_values("ordem").iloc[0]
    st.title("Visão executiva", anchor="visao-executiva")
    st.caption("Desempenho comercial · Vendas, produtos e padrões de compra")
    st.markdown(
        f"**Período completo:** {k['data_inicial']:%d/%m/%Y} — "
        f"{k['data_final']:%d/%m/%Y}"
    )
    st.info(
        "Valores monetários na unidade original da fonte. "
        "As seleções dos gráficos não alteram os KPIs globais."
    )
    for coluna, titulo, valor, definicao, origem in zip(
        st.columns(4),
        ["Receita total", "Pedidos realizados", "Unidades vendidas", "Ticket médio"],
        [
            painel.valor_monetario(k["receita"]),
            painel.numero(k["pedidos"]),
            painel.numero(k["unidades"]),
            painel.valor_monetario(k["ticket_medio"]),
        ],
        [
            "Receita registrada nos pedidos",
            "Um registro por pedido",
            "Cada ocorrência de item é uma unidade",
            "Receita total ÷ pedidos",
        ],
        [
            "10 · kpis.receita",
            "10 · kpis.pedidos",
            "10 · kpis.unidades",
            "10 · kpis.ticket_medio",
        ],
        strict=True,
    ):
        with coluna:
            cartao(titulo, valor, definicao, origem)
    apoios = st.columns(3)
    with apoios[0]:
        st.metric("Unidades por pedido", painel.numero(k["unidades_por_pedido"], 2))
        st.caption("10 · kpis.unidades_por_pedido")
    with apoios[1]:
        st.metric(
            "Clientes com mais de uma compra",
            painel.pct(dados["frequencia_clientes"].iloc[0]["proporcao_recompra"]),
        )
        st.caption("13 · frequencia_clientes.proporcao_recompra")
    with apoios[2]:
        st.metric("Produtos para atingir 80%", painel.numero(p["produtos_80"]))
        st.caption("08 · concentracao_pizzas.produtos_80")

    with st.container(border=True, key="caixa_mensal"):
        st.subheader("01 · Como as vendas evoluem?")
        st.caption("marts.vendas_mensais · mes / receita / pedidos")
        medida = st.radio("Série mensal", ["Receita", "Pedidos"], horizontal=True)
        campo = "receita" if medida == "Receita" else "pedidos"
        grafico(painel.vendas_mensais(dados["vendas_mensais"], campo), "mensal")
        meses = dados["vendas_mensais"].sort_values("mes")
        primeiro, ultimo = meses.iloc[0], meses.iloc[-1]
        fmt = painel.valor_monetario if campo == "receita" else painel.numero
        st.caption(
            f"De {fmt(primeiro[campo])} em {primeiro['mes']:%m/%Y} para "
            f"{fmt(ultimo[campo])} em {ultimo['mes']:%m/%Y}. "
            "Seleção válida somente para este gráfico."
        )

    st.header("O que sustenta a receita", anchor="produtos")
    esquerda, direita = st.columns(2)
    with esquerda, st.container(border=True, key="caixa_ranking"):
        modo = st.radio(
            "Ranking", ["Produtos consolidados", "Variantes (SKU)"], horizontal=True
        )
        sku = modo == "Variantes (SKU)"
        nome = "ranking_pizzas" if sku else "ranking_tipos_pizza"
        origem = "02" if sku else "11"
        st.subheader(f"{origem} · Produtos que lideram")
        st.caption(
            f"marts.{nome} · {'SKU' if sku else 'Name'} / receita · até nove líderes"
        )
        grafico(painel.ranking(dados[nome], sku), "ranking")
        lider = (
            dados[nome]
            .sort_values(["receita", "SKU" if sku else "Name"], ascending=[False, True])
            .iloc[0]
        )
        st.caption(
            f"{lider['Name']} lidera esta visão com receita de "
            f"{painel.valor_monetario(lider['receita'])}."
        )
    with direita, st.container(border=True, key="caixa_pareto"):
        st.subheader("08 · Concentração de vendas")
        st.caption("marts.concentracao_pizzas · receita / participacao_acumulada")
        st.markdown(
            f"**{painel.numero(p['produtos_80'])} produtos atingem "
            "ao menos 80% da receita.**"
        )
        grafico(painel.pareto(dados["concentracao_pizzas"]), "pareto")
        st.caption(
            f"{painel.pct(p['proporcao_produtos_80'])} dos produtos com vendas. "
            "Inclui o produto que cruza o corte; não presume uma relação 80/20."
        )

    st.header("Demanda e operação comercial", anchor="demanda-e-lojas")
    with st.container(border=True, key="caixa_horas"):
        st.subheader("04 · Pedidos por hora de São Paulo")
        st.caption(
            "marts.pedidos_hora · hora_local / pedidos · "
            "America/Sao_Paulo (UTC−03:00 em 2020–2022)"
        )
        grafico(painel.pedidos_hora(dados["pedidos_hora"]), "horas")
        sem_hora = dados["pedidos_hora"].loc[
            dados["pedidos_hora"]["hora_nao_informada"]
        ]
        if not sem_hora.empty:
            st.caption(
                f"Sem horário informado: {painel.numero(sem_hora.iloc[0]['pedidos'])} "
                "pedidos, preservados no total."
            )
        conhecidas = dados["pedidos_hora"].loc[
            dados["pedidos_hora"]["hora_local"].notna()
        ]
        if not conhecidas.empty:
            pico = conhecidas.sort_values(
                ["pedidos", "hora_local"], ascending=[False, True]
            ).iloc[0]
            st.caption(
                f"{int(pico['hora_local']):02}h tem o maior volume: "
                f"{painel.numero(pico['pedidos'])} pedidos. "
                "Referência de visualização; "
                "não é o fuso comercial das lojas americanas."
            )

    colunas = st.columns(3)
    with colunas[0], st.container(border=True, key="caixa_semana"):
        st.subheader("03 · Quando os clientes compram?")
        st.caption("marts.pedidos_dia_semana · dia_iso / pedidos")
        grafico(painel.pedidos_semana(dados["pedidos_dia_semana"]), "semana")
        pico = (
            dados["pedidos_dia_semana"]
            .sort_values(["pedidos", "dia_iso"], ascending=[False, True])
            .iloc[0]
        )
        st.caption(
            f"{painel.DIAS[int(pico['dia_iso'])]} lidera: "
            f"{painel.numero(pico['pedidos'])} pedidos. "
            "Volume acumulado, não média por dia aberto."
        )
    with colunas[1], st.container(border=True, key="caixa_categorias"):
        st.subheader("06 · Mix de categorias")
        st.caption("marts.receita_categoria · Category / receita")
        grafico(painel.categorias(dados["receita_categoria"]), "categorias")
        lider = (
            dados["receita_categoria"]
            .sort_values(["receita", "Category"], ascending=[False, True])
            .iloc[0]
        )
        st.caption(
            f"{lider['Category']} lidera com receita de "
            f"{painel.valor_monetario(lider['receita'])}."
        )
    with colunas[2], st.container(border=True, key="caixa_lojas"):
        st.subheader("12 · Lojas em destaque")
        st.caption("marts.vendas_loja · storeId / receita · cinco líderes")
        grafico(painel.lojas(dados["vendas_loja"]), "lojas")
        lider = (
            dados["vendas_loja"]
            .sort_values(["receita", "storeId"], ascending=[False, True])
            .iloc[0]
        )
        st.caption(
            f"{lider['storeId']}, em {lider['city']}, lidera com "
            f"{painel.valor_monetario(lider['receita'])}."
        )

    st.header("Uma leitura correta dos indicadores", anchor="sobre-os-dados")
    st.markdown("""
    - Dados inteiramente fictícios de Pizza Paradise / Observable; valores na
      unidade monetária original, sem moeda declarada nos anexos.
    - Todos os KPIs representam o período completo. Recompra é frequência
      observada, não retenção comprovada.
    - Horas usam São Paulo como referência; dias e meses mantêm a data original
      da fonte. Pedidos sem hora continuam no total.
    - Sem custos, status ou eventos logísticos, não é possível afirmar margem,
      cancelamento ou prazo de entrega.
    """)
    with st.expander("Consultar medidas completas dos marts"):
        tabela = st.selectbox("Mart", list(dados))
        st.dataframe(dados[tabela], width="stretch", hide_index=True)
    st.caption(
        "Pizza Paradise · Streamlit / Plotly · Fonte: Observable · "
        "Somente marts auditados"
    )


if __name__ == "__main__":
    main()
