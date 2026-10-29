# Etapa 4 — Dashboard Pizza Paradise

Status: implementado e conferido em 29/10/2026; desenho validado antes do código.
Rascunho e PNG preservados. Resultados em docs/execucao-dashboard.md.

## CONTEXTO

Treze marts validados. Criar visão executiva com Streamlit e Plotly, usando
Python 3.13 e DuckDB local. Nesta entrega: protótipo em HTML e rascunho PNG.
O protótipo não substitui app.py e não executa o pipeline.

## STACK

Python 3.13, uv, DuckDB, Streamlit e Plotly na versão funcional. O rascunho
usa HTML/CSS/SVG/JavaScript local; Playwright/Chromium somente para a captura.

## O QUE JÁ EXISTE (use, não reimplemente)

Somente SELECT em marts, conexão read_only fechada após leitura.
design/dados.js contém um retrato dos marts agregados, sem dados individuais;
design/rascunho.html apresenta esse retrato sem dependências externas.
design/rascunho.png é captura real do HTML renderizado a 1440 px de largura,
com a página completa para preservar a leitura. Não representa app Streamlit.
scripts/preparar_rascunho.py atualiza dados.js com SELECTs em marts, sem fórmulas.
Metadados registram data da leitura, tabelas e hashes dos artefatos gerados.
No produto futuro: painel.py para leitura/formatação/gráficos, app.py para UI.

## ARTEFATOS A PRODUZIR

painel.py sem Streamlit; app.py executável com uv run streamlit run app.py;
.streamlit/config.toml com o tema aprovado; test/test_painel.py com dados
sintéticos. Nesta entrega, não implementar relatorio.py: fica como extensão
opcional reutilizando as figuras, sem criar placeholders.

## SPEC

### 1. LEITURA

Somente SELECT em marts; conexão read_only fechada na função de leitura.
HTML recebe snapshot estático de agregados. Motivo: liberar banco para escrita
e manter a tela separada do cálculo dos indicadores.
painel.ler(banco=None) consulta os dez marts usados: kpis, vendas_mensais,
ranking_tipos_pizza, ranking_pizzas, concentracao_pizzas, pedidos_dia_semana,
pedidos_hora, receita_categoria, vendas_loja e frequencia_clientes. Não carregar
as bases por pedido com milhões de linhas. Usar fetchall para preservar Decimal
ao construir DataFrames. Validar tabelas/colunas obrigatórias e fontes não vazias;
um erro lista as fontes afetadas, sem números de fallback.

### 2. NENHUM CÁLCULO

Não criar indicadores por groupby, sum, mean, count, merge ou pivot na tela.
Permitidos ordenar, selecionar linhas, formatar e escalar coordenadas visuais.
Motivo: toda fórmula tem seu SQL rastreável e o mesmo resultado nas interfaces.

### 3. LAYOUT (de cima para baixo)

Fundo #ECFEFF, cartões brancos, texto #164E63 e destaque #0891B2. Rótulos claros,
foco visível e layout responsivo. Mostrar período completo e dados fictícios.
Quatro KPIs: receita, pedidos, unidades e ticket; apoios de cesta, frequência
observada e Pareto. Cada caixa identifica NN/mart e medida, cada gráfico traz
uma frase-resposta. Receita principal completa; nomes originais como texto.

Faixas: sete KPIs principais/auxiliares; evolução mensal (01); ranking (11)
e Pareto (08); horas (04), dia da semana (03), categorias (06) e lojas (12).
Motivo: primeiro tamanho das vendas, depois evolução e composição.
No Pareto, Name original inclinado no eixo X, sem posições numéricas isoladas.
Manter ordem, participações e grupo de 80% do mart, sem recalcular o corte.
Permitir alternar ranking consolidado (11) e variantes SKU (02), exibindo até
nove primeiros por receita. Isso é seleção de exibição, sem alterar os KPIs.
Pico horário, líder de produto/categoria/loja são seleção/ordenação de linhas
existentes, sem criar médias ou percentuais. Mostrar definições e medidas
completas em tabelas expansíveis. O filtro global de datas continua ausente.

### 4. FORMATO

Milhar com ponto, decimal com vírgula, receita/ticket com duas casas e percentuais
identificados. Não depender do locale do sistema nem afirmar USD/BRL sem fonte.
Na versão funcional, funções puras em painel.py: numero(valor, casas=0),
pct(valor, casas=1) e valor_monetario(valor, casas=2), sem símbolo não comprovado.
Uma função por gráfico recebe DataFrame e retorna figura Plotly; app.py usa
layout="wide" e gráficos com width="stretch". Motivo: reutilizar as mesmas
funções em Streamlit/HTML e testar formato sem banco ou interface.
Hora exibida vem de hora_local e fuso_horario do mart: America/Sao_Paulo,
UTC−03:00 em 2020–2022. É referência comum de visualização, não o fuso comercial
das lojas americanas. Motivo: distinguir dado original e representação escolhida.

### 5. FILTROS E ERROS

Navegação e seleção de série não mudam KPIs globais. Sem filtro global de período
ou loja. Campo/tabela ausente ou consulta inválida mostra erro, nunca zeros
inventados. Mudança de população exige revisar marts antes de alterar a tela.
Motivo: comparações precisam da mesma janela e dos mesmos denominadores.

### 6. CACHE E ERRO

Snapshot atualizado por scripts/preparar_rascunho.py; PNG capturado por
scripts/capturar_rascunho.py. Na versão funcional, recarga explícita deve reler
os marts sem conexão global. Streamlit futuro usa st.cache_data e botão
"Recarregar dados" que limpa o cache. Banco/mart ausente: st.error informa quais
fontes faltam e o comando uv run python -m pipeline.marts; st.stop() interrompe.
Motivo: os números não podem ficar antigos nem ausentes sem aviso.

## CRITÉRIOS DE ACEITE

HTML abre localmente, sem rede, com navegação e alternância de série funcionais.
KPIs correspondem ao retrato dos marts; formatação pt-BR e unidades explícitas.
Gráficos identificam eixos, período e medidas. Valores completos acessíveis
por texto/detalhes, além das abreviações. PNG existe antes da implementação
Streamlit. Não alterar banco, pipeline ou marts para gerar o desenho.
Verificar no Chromium: números vs SELECTs, ausência de erros JavaScript,
alternância mensal, navegação e largura móvel de 390 px sem transbordamento.
PNG gerado por captura do HTML com seus dados carregados, sem desenho substituto.
Pareto identifica os nove nomes sem cortes e preserva leitura em detalhes/tooltip.
Horas de 00:00 UTC em 2020 são 21:00 em São Paulo; sem hora mantém NULL.
Na versão funcional, testes sintéticos de formatos e cobertura incluindo painel.py.
Conferir Streamlit no navegador: sete gráficos, origem de cada medida, Pareto
com nomes, variantes/consolidado, série mensal, recarga e viewport móvel. Com
servidor aberto, pipeline.marts deve executar sem erro de lock; recarregar
o painel e comparar KPIs com os marts. Capturas/evidências em docs/, sem rede
ou banco real na suíte unitária.

## ENTREGA

Desenho validado com usuário antes da implementação Streamlit. Filtros futuros
que alterem a população exigem revisão dos marts, não regras ocultas no painel.
Moeda declarada segue pendente. Horas usam São Paulo por decisão de 29/10/2026;
refined conserva timestamp UTC. Dias/meses permanecem pela data original da fonte.
Transformação/marts registrados em commits locais na revisão de versionamento;
não retrodatá-los nem afirmar que foram criados antes de desenvolver.
Entregar docstrings com as regras/motivos, código e lista de suposições não
previstas. Resultados de execução ficam em docs/, sem transformar números antigos
em critérios universais ou declarar Streamlit pronto a partir do protótipo.
