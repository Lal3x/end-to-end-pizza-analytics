# Dashboard Streamlit — execução e validação

Data: 29/10/2026. [Contrato](../specs/dashboard.md) e
[rascunho aprovado](../design/rascunho.png).

## Entrega

painel.py lê dez marts agregados com SELECT e conexão read_only fechada;
preserva Decimal no DataFrame, formata valores em pt-BR e devolve figuras Plotly.
app.py organiza o layout, cache, navegação e seleções. Tema ciano definido em
.streamlit/config.toml, com cartões brancos e barra lateral azul escura.

Quatro KPIs principais, três auxiliares e sete gráficos. Ranking alterna produto
consolidado/variante SKU e mostra até nove líderes; seleção mensal alterna
receita/pedidos. Nenhuma interação recalcula KPIs globais. Pareto identifica
nomes, acumulado pronto e linha de 80%; horas usam São Paulo e preservam o grupo
sem horário. Tabelas expansíveis dão acesso às medidas completas.

Não há consultas a raw/refined, bases com milhões de pedidos na memória da UI,
agregação de negócio no pandas ou conexão global no cache. Não foi acrescentada
dependência ao projeto. Relatório HTML final não integra esta entrega opcional.

## Como executar

Com os marts publicados e ui.py encerrado:

```bash
uv run streamlit run app.py
```

Endereço padrão: http://localhost:8501. Após uma nova carga de marts, clicar em
**Recarregar dados**. Banco/mart ausente informa a causa e orienta executar
uv run python -m pipeline.marts, sem criar arquivo vazio ou números de fallback.

Nesta sessão o servidor foi iniciado na porta 8502 com o ambiente instalado:

```bash
.venv/bin/python -m streamlit run app.py --server.port 8502 --server.address 127.0.0.1 --browser.gatherUsageStats false
```

O primeiro início no sandbox falhou por restrição à abertura de socket;
o início autorizado funcionou. O servidor permaneceu aberto na verificação.

## Resultados observados

Os quatro cartões foram comparados no Chromium com SELECT direto dos marts:
receita 50.211.527,85; pedidos 2.046.713; unidades 2.916.015; ticket 24,53.
Sem símbolo de moeda não comprovado. Sete gráficos renderizados, nomes do
Pareto iguais ao mart e pico horário de 21h de São Paulo; 116 sem horário.

Alternância mensal, ranking por SKU, retorno ao consolidado e recarga funcionam.
Com navegador e servidor ativos, pipeline.marts executou em 4,740 s na verificação
final, sem erro
de lock. Após recarga, os KPIs continuaram iguais. Navegador sem erros JavaScript;
viewports 1440 × 1024 e 390 × 844 sem transbordamento horizontal ou KPIs cortados.

[Evidência JSON](evidencias/dashboard-verificacao.json),
[desktop](evidencias/dashboard-desktop.png) e
[móvel](evidencias/dashboard-mobile.png). As imagens são capturas dos viewports
do aplicativo, não uma exportação de relatório HTML completo.
Capturas adicionais: [produtos](evidencias/dashboard-produtos.png) e
[demanda](evidencias/dashboard-demanda.png).

A primeira automação tentou clicar diretamente no input dos radios estilizados
e falhou por interceptação do rótulo. A verificação passou ao clicar no rótulo
visível, sem forçar interação através da interface. A falha não foi ignorada
nem substituída por manipulação dos valores dos widgets via JavaScript.

## Testes

.venv/bin/pytest --cov: 112 testes passaram em 13,63 s. Cobertura 94,05% de
521 linhas; painel.py com suas 112 linhas executáveis cobertas. Os 25 testes
novos usam valores inventados e DuckDB temporário real, inclusive AppTest para
erro de fonte e cache/recarga. Nenhum teste unitário depende do banco do projeto.

Incluem formatos exatos sem locale/perda de centavos, entradas inválidas,
Decimal na leitura, conexão liberada para escrita, fontes/colunas faltantes,
medidas originais nos gráficos, variantes, nomes do Pareto e ausência de hora.
AppTest prova que mudança no banco permanece em cache até clicar em recarregar.

Ruff check, format check e git diff --check aprovados. Busca por operações de
agregação/junção de negócio em painel.py/app.py não encontrou ocorrências.
Para repetir a revisão com servidor aberto:

```bash
uv run --with playwright python scripts/verificar_dashboard.py --iniciar-servidor
```

Esse comando é integração visual com o banco real, fora da suíte unitária;
inicia e encerra um servidor temporário próprio na porta 8502, reexecuta os marts
e gera capturas de viewport/seções e o JSON de evidência. Sem a opção
--iniciar-servidor, usa um servidor já aberto em --url.
Playwright/Chromium são ferramentas temporárias, sem modificar o lockfile.

## Limites e versionamento

Período completo; sem filtros globais de data/loja nem indicadores de crescimento,
margem ou entrega. Moeda da fonte segue sem declaração explícita. Horas de
São Paulo são referência escolhida, não fuso comercial das lojas americanas.
Dados são inteiramente fictícios. Relatório HTML reutilizável pode ser uma
extensão posterior, não um arquivo vazio para aparentar entrega.

O usuário autorizou organizar os commits pendentes e implementar o painel.
As alterações acumuladas são registradas agora por conteúdo: simplificação,
transformação, marts, desenho/specs e dashboard. Todos usam as datas reais;
isso não reconstrói uma cronologia de commits anteriores ao desenvolvimento.
README, plano e metodologia descrevem o estado final, não commits fictícios.
