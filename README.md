# Pizza Analytics

Pipeline autoral de Engenharia de Dados para analisar vendas com os dados
inteiramente fictícios do **Pizza Paradise / Observable**.

Python 3.13 · uv · pandas · DuckDB · SQL · pytest · Ruff · Streamlit · Plotly

[Documentação](https://lal3x.github.io/end-to-end-pizza-analytics/) ·
[Guia local](docs/guia-rapido.md) · [Critérios de entrega](docs/entrega.md)

O endereço da documentação será ativado pelo workflow após publicar e integrar
esta configuração na main; build local não significa site já publicado.

## O que o projeto responde

Quanto vendeu, como as vendas evoluíram, quais produtos/categorias/tamanhos
lideraram, quando os pedidos se concentraram, qual o ticket e quantos produtos
atingem 80% da receita. Também compara lojas e frequência de compra.

[Contratos dos 13 indicadores](docs/contratos-indicadores.md). Não há dados para
afirmar margem, cancelamento ou prazo de entrega. Moeda não declarada nos anexos;
usar unidade original. Horas em São Paulo como referência escolhida, não fuso
comercial das lojas; mês/dia mantêm a data original da fonte.

## Fonte, grãos e arquitetura

Fonte: [Pizza Paradise](https://observablehq.com/@observablehq/pizza-paradise-data),
gerado pela equipe Observable; notebook de Paul Buffa, versão 398.
Permissão textual ampla, sem licença padronizada nos metadados dos cinco anexos.
Não atribuir CC0/ISC nem redistribuir os anexos completos neste repositório.
[Proveniência e política de publicação](docs/fontes-e-licenca.md).

| Tabela | Uma linha representa | Chave |
|---|---|---|
| orders | Um pedido | id |
| order_items | Uma ocorrência de produto no pedido | Sem PK natural de linha |
| products | Uma variante de pizza | SKU |
| customers | Um cliente fictício | id |
| stores | Uma loja | id |

FKs: orders.customerId → customers.id; orders.storeId → stores.id;
order_items.orderID → orders.id; order_items.SKU → products.SKU.
[Modelo completo](docs/modelo.md).

```text
Arquivos CSV/Parquet → raw/pizza_paradise/
  → pizza.duckdb: raw → refined → marts → dashboard

pipeline/ingestao.py       preservação dos dados
pipeline/transformacao.py  conversões/validações pandas
pipeline/marts.py         execução dos 13 SQLs e auditorias
db.py                     conexão compartilhada
baixar_dados.py            aquisição independente
executar_pipeline.py      transação única das três etapas
painel.py / app.py         leitura, formatos, Plotly / interface Streamlit
```

CSV textual e Parquet nativo na RAW. Na refined, IDs VARCHAR e dinheiro
DECIMAL(18,2); formatos temporais explícitos, correção restrita de Launch e
duplicatas exatas removidas somente nas tabelas com PK. As 54.041 repetições
legítimas de itens são preservadas. Receita soma Price por ocorrência e
reconcilia com total do pedido; ticket parte de uma linha por pedido.
Specs em [specs/](specs/) e [decisões de transformação](specs/transformacao.md).

## Executar do zero

Linux/WSL, Git e uv. Python 3.13 e dependências são resolvidos pelo projeto.
Windows nativo não foi validado; a medição de memória usa resource (Unix).

```bash
git clone https://github.com/Lal3x/end-to-end-pizza-analytics.git
cd end-to-end-pizza-analytics
uv sync --locked --group docs
uv run python baixar_dados.py
uv run python executar_pipeline.py
uv run streamlit run app.py
```

Abrir http://localhost:8501. Encerrar ui.py antes de gravar no banco; após nova
carga, clicar em **Recarregar dados**. O executor não inicia interfaces, não
baixa fontes e só publica após concluir todas as auditorias. Em falha tratável
antes do commit, reverte o conjunto e preserva outros schemas.

Ensaio isolado: `uv run python executar_pipeline.py --banco data/ensaio.duckdb`.
[Detalhes operacionais](docs/execucao-pipeline.md) e
[comandos individuais](docs/guia-rapido.md#comandos-individuais).

## Qualidade e desenvolvimento

```bash
uv run pre-commit install
uv run pre-commit run --all-files
uv run pytest --cov
uv run ruff check .
uv run ruff format --check .
uv run mkdocs build --strict
uv run mkdocs serve
```

Testes usam fontes sintéticas e DuckDB temporário real, sem rede ou banco do
projeto. No executor: **127 testes, cobertura 94,81%**, meta ≥60%.
Verificações independentes conferem PKs, FKs, nulos, tipos, grãos e receitas.
[CI, hooks e publicação](docs/automacao.md).

CI valida push/PR com uv.lock, hooks, testes e build estrito. Na main, CD publica
somente o site estático no GitHub Pages após qualidade aprovada. O Pages não
executa o servidor Streamlit. [Workflow](.github/workflows/ci.yml).

## Resultados verificados

2.046.713 pedidos, 2.916.015 itens, 34.761 clientes, 32 lojas e 36 SKUs em
2020–2022. Cinco RAW, cinco refined, treze marts. Ensaio/reexecução/carga
principal comparados integralmente com zero diferenças. A carga completa levou
53,848 s e pico RSS de 1.931,85 MiB nesta máquina; não é garantia para outra base.

[Pipeline completo](docs/execucao-pipeline.md) ·
[Dashboard validado](docs/execucao-dashboard.md) ·
[PNG do rascunho](design/rascunho.png) ·
[Captura funcional](docs/evidencias/dashboard-desktop.png)

Arquivos brutos, banco, backups, credenciais, caches, site gerado e AGENTS.md
ficam fora do Git. Evidências pequenas, agregados e imagens são artefatos de
revisão.

## Decisões técnicas e participação da IA

O autor criou e validou as specs, tomou as decisões de negócio e definiu os
indicadores. Conduziu o escopo e a escolha da fonte Pizza Paradise,
exigiu transformação com pandas e simplificou a estrutura de pipeline/.
Aprovou regras de conversão antes do código, solicitou Pareto e análises
separadas por SKU e nome, escolheu o horário de São Paulo e orientou a revisão
visual. Também solicitou o executor completo, CI, hooks e documentação.
[Decisões e limitações](docs/decisoes.md).

Codex apoiou a investigação, o detalhamento das specs, a implementação e os
testes, sob orientação e revisão do autor. Desvios efetivamente
encontrados: estrutura excessiva e transformação SQL contrariando a escolha por
pandas; inferência Decimal do DuckDB insuficiente; formatos de data distintos e
repetições de itens legítimas; layout/fuso corrigidos após revisão do usuário.
As correções e evidências estão na [metodologia](docs/metodologia.md).

Algumas mudanças ficaram acumuladas antes de serem registradas em commits;
não foram retrodatadas. O histórico real foi preservado. As decisões e os
resultados relatados correspondem às verificações efetivamente realizadas.
