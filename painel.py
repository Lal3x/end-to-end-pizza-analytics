"""Leitura, formatos e figuras conforme specs/dashboard.md, sem Streamlit.

Lê somente marts em conexão read_only fechada antes de devolver os dados.
Não agrega, junta ou recalcula indicadores: ordenação/seleção são apresentação.
Dinheiro permanece Decimal até a renderização; gráficos recebem medidas prontas.
Funções de formato são puras e independem de banco, locale ou interface.
"""

from decimal import Decimal, InvalidOperation
from pathlib import Path

import duckdb
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

BANCO = Path(__file__).resolve().parent / "pizza.duckdb"
COLUNAS = {
    "kpis": {
        "pedidos",
        "unidades",
        "receita",
        "ticket_medio",
        "unidades_por_pedido",
        "data_inicial",
        "data_final",
    },
    "vendas_mensais": {"mes", "receita", "pedidos"},
    "ranking_tipos_pizza": {"Name", "receita", "posicao"},
    "ranking_pizzas": {"SKU", "Name", "Size", "receita", "posicao"},
    "concentracao_pizzas": {
        "Name",
        "receita",
        "ordem",
        "participacao_acumulada",
        "grupo_80",
        "produtos_80",
        "proporcao_produtos_80",
    },
    "pedidos_dia_semana": {"dia_iso", "pedidos"},
    "pedidos_hora": {"hora_local", "fuso_horario", "hora_nao_informada", "pedidos"},
    "receita_categoria": {"Category", "receita"},
    "vendas_loja": {"storeId", "city", "state", "receita"},
    "frequencia_clientes": {"frequencia", "clientes", "proporcao_recompra"},
}
COR = "#0891B2"
TEXTO = "#164E63"
DIAS = {
    1: "Segunda",
    2: "Terça",
    3: "Quarta",
    4: "Quinta",
    5: "Sexta",
    6: "Sábado",
    7: "Domingo",
}


def ler(banco: Path | None = None) -> dict[str, pd.DataFrame]:
    """Lê os dez marts agregados e fecha a conexão antes do retorno.

    Args:
        banco: Arquivo existente; padrão pizza.duckdb junto ao módulo.

    Returns:
        DataFrames por nome de mart, preservando dinheiro como Decimal.

    Raises:
        FileNotFoundError: Se o banco não existir; não cria um arquivo vazio.
        ValueError: Se houver tabelas ausentes/vazias ou colunas faltantes.
        duckdb.Error: Se a conexão ou outra consulta falhar.
    """
    caminho = Path(banco) if banco is not None else BANCO
    if not caminho.is_file():
        raise FileNotFoundError(f"Banco ausente: {caminho}")
    dados, erros = {}, []
    with duckdb.connect(str(caminho), read_only=True) as con:
        for nome, obrigatorias in COLUNAS.items():
            try:
                cursor = con.execute(f"SELECT * FROM marts.{nome}")
            except duckdb.CatalogException:
                erros.append(f"marts.{nome}: tabela ausente")
                continue
            colunas = [c[0] for c in cursor.description]
            faltantes = obrigatorias.difference(colunas)
            if faltantes:
                erros.append(f"marts.{nome}: colunas ausentes {sorted(faltantes)}")
                continue
            linhas = cursor.fetchall()
            if not linhas:
                erros.append(f"marts.{nome}: tabela vazia")
                continue
            dados[nome] = pd.DataFrame(linhas, columns=colunas)
    if erros:
        raise ValueError("; ".join(erros))
    return dados


def numero(valor, casas: int = 0) -> str:
    """Formata número finito em pt-BR, preservando Decimal sem passar por float.

    Raises:
        ValueError: Se não for número finito ou casas estiver fora de 0–6.
    """
    if isinstance(casas, bool) or not isinstance(casas, int) or not 0 <= casas <= 6:
        raise ValueError("casas deve ser inteiro entre 0 e 6")
    try:
        decimal = Decimal(str(valor))
    except (InvalidOperation, ValueError) as erro:
        raise ValueError(f"Número inválido: {valor!r}") from erro
    if not decimal.is_finite():
        raise ValueError(f"Número não finito: {valor!r}")
    return f"{decimal:,.{casas}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def valor_monetario(valor, casas: int = 2) -> str:
    """Formata a unidade monetária original, sem inventar símbolo de moeda."""
    return numero(valor, casas)


def pct(valor, casas: int = 1) -> str:
    """Exibe uma proporção pronta do mart como percentual, sem novo indicador."""
    try:
        percentual = Decimal(str(valor)) * 100
    except InvalidOperation as erro:
        raise ValueError(f"Proporção inválida: {valor!r}") from erro
    return numero(percentual, casas) + "%"


def _estilo(fig: go.Figure, eixo_x: str, eixo_y: str, altura: int = 380) -> go.Figure:
    """Aplica somente aparência e unidades, sem alterar medidas dos gráficos."""
    fig.update_layout(
        template="plotly_white",
        height=altura,
        font={"family": "Arial, sans-serif", "color": TEXTO, "size": 12},
        paper_bgcolor="white",
        plot_bgcolor="white",
        separators=",.",
        margin={"l": 35, "r": 25, "t": 20, "b": 50},
        showlegend=False,
    )
    fig.update_xaxes(title_text=eixo_x, showgrid=False, automargin=True)
    fig.update_yaxes(title_text=eixo_y, gridcolor="#EAF2F4", automargin=True)
    return fig


def vendas_mensais(dados: pd.DataFrame, medida: str = "receita") -> go.Figure:
    """Desenha meses observados; seleção de série não recalcula KPIs globais."""
    if medida not in {"receita", "pedidos"}:
        raise ValueError("Medida mensal deve ser receita ou pedidos")
    df = dados.sort_values("mes")
    formato = valor_monetario if medida == "receita" else numero
    fig = go.Figure(
        go.Scatter(
            x=df["mes"],
            y=df[medida],
            mode="lines+markers",
            line={"color": COR, "width": 3},
            marker={"size": 5},
            fill="tozeroy",
            fillcolor="rgba(8,145,178,0.09)",
            customdata=[formato(v) for v in df[medida]],
            hovertemplate="%{x|%m/%Y}<br>%{customdata}<extra></extra>",
        )
    )
    _estilo(
        fig,
        "Mês de registro da fonte",
        "Receita · unidade original" if medida == "receita" else "Pedidos",
    )
    fig.update_xaxes(type="date", dtick="M6", tickformat="%m/%Y")
    fig.update_yaxes(rangemode="tozero", tickformat=",.0f")
    return fig


def ranking(dados: pd.DataFrame, por_sku: bool = False) -> go.Figure:
    """Exibe até nove líderes, preservando ranking/receita prontos no mart."""
    chave = "SKU" if por_sku else "Name"
    df = dados.sort_values(["receita", chave], ascending=[False, True]).head(9)
    hover = [
        [
            str(r.Name),
            valor_monetario(r.receita),
            str(r.Size) if por_sku else "Todos os tamanhos",
        ]
        for r in df.itertuples()
    ]
    fig = go.Figure(
        go.Bar(
            x=df["receita"],
            y=df[chave],
            orientation="h",
            marker_color=COR,
            customdata=hover,
            hovertemplate=(
                "%{customdata[0]}<br>%{customdata[2]}<br>"
                "Receita: %{customdata[1]}<extra></extra>"
            ),
        )
    )
    _estilo(fig, "Receita · unidade original", "SKU" if por_sku else "Produto", 490)
    fig.update_yaxes(
        categoryorder="array", categoryarray=df[chave].tolist(), autorange="reversed"
    )
    return fig


def pareto(dados: pd.DataFrame) -> go.Figure:
    """Desenha receita e percentual acumulado do mart, com nomes no eixo X."""
    df = dados.sort_values("ordem")
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            name="Receita",
            x=df["Name"],
            y=df["receita"],
            marker_color=[COR if flag else "#B9E4ED" for flag in df["grupo_80"]],
            customdata=[valor_monetario(v) for v in df["receita"]],
            hovertemplate="%{x}<br>Receita: %{customdata}<extra></extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            name="Receita acumulada",
            x=df["Name"],
            y=df["participacao_acumulada"],
            line={"color": TEXTO, "width": 3},
            mode="lines+markers",
            customdata=[pct(v) for v in df["participacao_acumulada"]],
            hovertemplate="%{x}<br>Acumulado: %{customdata}<extra></extra>",
        ),
        secondary_y=True,
    )
    _estilo(
        fig,
        "Produtos · ordem decrescente de receita",
        "Receita · unidade original",
        540,
    )
    fig.update_xaxes(
        tickangle=-55, categoryorder="array", categoryarray=df["Name"].tolist()
    )
    fig.update_yaxes(
        title_text="Receita acumulada",
        range=[0, 1.05],
        tickformat=".0%",
        tickmode="array",
        tickvals=[0, 0.2, 0.4, 0.6, 0.8, 1],
        showgrid=False,
        secondary_y=True,
    )
    fig.add_hline(
        y=0.8,
        line_dash="dash",
        line_color="#64748B",
        secondary_y=True,
    )
    fig.update_layout(margin={"b": 155})
    return fig


def pedidos_hora(dados: pd.DataFrame) -> go.Figure:
    """Mostra horas de São Paulo conhecidas; NULL permanece fora das barras."""
    df = dados.loc[dados["hora_local"].notna()].sort_values("hora_local")
    fig = go.Figure(
        go.Bar(
            x=[f"{int(v):02}h" for v in df["hora_local"]],
            y=df["pedidos"],
            marker_color=COR,
            customdata=[numero(v) for v in df["pedidos"]],
            hovertemplate="%{x} · São Paulo<br>%{customdata} pedidos<extra></extra>",
        )
    )
    _estilo(fig, "Hora de São Paulo · America/Sao_Paulo", "Pedidos")
    fig.update_xaxes(type="category")
    if df.empty:
        fig.add_annotation(text="Nenhum horário informado", showarrow=False)
    return fig


def pedidos_semana(dados: pd.DataFrame) -> go.Figure:
    """Exibe volumes observados por dia ISO da data original da fonte."""
    df = dados.sort_values("dia_iso")
    fig = go.Figure(
        go.Bar(
            x=[DIAS[int(v)] for v in df["dia_iso"]],
            y=df["pedidos"],
            marker_color=COR,
            customdata=[numero(v) for v in df["pedidos"]],
            hovertemplate="%{x}<br>%{customdata} pedidos<extra></extra>",
        )
    )
    return _estilo(fig, "Dia da semana · data original", "Pedidos")


def categorias(dados: pd.DataFrame) -> go.Figure:
    """Mostra a receita por categoria na classificação original do catálogo."""
    df = dados.sort_values(["receita", "Category"], ascending=[False, True])
    fig = go.Figure(
        go.Bar(
            x=df["receita"],
            y=df["Category"],
            orientation="h",
            marker_color=COR,
            customdata=[valor_monetario(v) for v in df["receita"]],
            hovertemplate="%{y}<br>Receita: %{customdata}<extra></extra>",
        )
    )
    _estilo(fig, "Receita · unidade original", "Categoria")
    fig.update_yaxes(
        categoryorder="array",
        categoryarray=df["Category"].tolist(),
        autorange="reversed",
    )
    return fig


def lojas(dados: pd.DataFrame) -> go.Figure:
    """Seleciona cinco lojas por receita; não altera nenhum total do painel."""
    df = dados.sort_values(["receita", "storeId"], ascending=[False, True]).head(5)
    fig = go.Figure(
        go.Bar(
            x=df["receita"],
            y=df["storeId"],
            orientation="h",
            marker_color=COR,
            customdata=[
                [r.city, r.state, valor_monetario(r.receita)] for r in df.itertuples()
            ],
            hovertemplate=(
                "%{y} · %{customdata[0]}<br>%{customdata[1]}<br>"
                "Receita: %{customdata[2]}<extra></extra>"
            ),
        )
    )
    _estilo(fig, "Receita · unidade original", "Loja")
    fig.update_yaxes(
        categoryorder="array",
        categoryarray=df["storeId"].tolist(),
        autorange="reversed",
    )
    return fig
