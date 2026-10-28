# Pizza — análise de vendas com engenharia de dados

**Status: Etapa Zero preparada para revisão.** O pipeline e o dashboard ainda
não foram implementados. Este repositório de trabalho investiga dados de uma
pizzaria fictícia para responder quanto vendeu, como evoluíram as vendas, quais
produtos lideram e quando se concentram os pedidos.

O desenvolvimento segue o método spec-driven do curso Pipeline Olist, com
decisões e critérios antes do código. A [análise das quatro aulas](docs/metodologia.md)
explica como o método foi adaptado a este conjunto de dados.

## Fonte e licença

Dados: Neethi Mohan / [Kaggle, Maven Pizza Challenge Dataset v1](https://www.kaggle.com/datasets/neethimohan/maven-pizza-challenge-dataset),
licença declarada **CC0: Public Domain**, conferida na API da própria
republicação em 28/10/2026. Contexto original:
[Maven Analytics, Pizza Place Sales](https://mavenanalytics.io/data-playground/pizza-place-sales).
Consulte [proveniência, evidência e limites da licença](docs/fontes-e-licenca.md).

ZIP, CSVs e banco ficam ignorados pelo Git. Nenhum dado ou projeto foi publicado.
A licença autoral do código será escolhida antes da publicação.

## Modelo e arquitetura propostos

```text
Kaggle v1 → raw/ (CSV preservado)
                 ↓ ingestão futura
            pizza.duckdb: raw.* (VARCHAR)
                 ↓ transformação futura
            refined.* (tipos e integridade)
                 ↓ SQL futuro em sql/marts/NN_nome.sql
            marts.* (indicadores)
                 ↓ SELECT read_only
            painel.py / app.py (futuros)
```

| Tabela | Uma linha representa | PK | FK |
|---|---|---|---|
| orders | Pedido registrado por uma mesa | order_id | — |
| order_details | Variante de pizza dentro de um pedido, com quantidade | order_details_id | order_id → orders; pizza_id → pizzas |
| pizzas | Variante de tipo e tamanho | pizza_id | pizza_type_id → pizza_types |
| pizza_types | Tipo de pizza do cardápio | pizza_type_id | — |

O [modelo detalhado](docs/modelo.md) contém colunas, cardinalidades, diagrama e
tipos propostos. IDs continuam texto, datas viram DATE, horas TIME, quantidades
INTEGER e preço DECIMAL(10,2). Não foi encontrada necessidade de limpeza na v1.
As [decisões de transformação](specs/transformacao.md) aguardam revisão.

## Indicadores e limites

[indicadores.md](indicadores.md) lista onze candidatos no formato da aula 1:
indicador — tabelas e colunas — o que mede. As definições de população,
fórmulas, grãos e critérios estão nos
[contratos analíticos propostos](docs/contratos-indicadores.md): vendas mensais,
rankings por variante e consolidado por tipo, pedidos por dia da
semana e hora, receita por pedido, categoria e tamanho, concentração de receita,
quantidade por pedido e KPIs gerais.

Receita estimada = `SUM(quantity * price)`, em **USD**, moeda declarada no
dicionário. Ticket médio parte de uma linha de receita por pedido. O preço é
de catálogo, sem histórico transacional: sua aplicação a todas as vendas é
uma hipótese aprovada pelo usuário, mantendo a limitação histórica. A seleção
e as definições dos indicadores continuam em revisão conjunta.
Não há custo, cliente, status, estoque ou eventos
de entrega; não será possível afirmar lucro, clientes únicos ou cancelamento.
Um ano observado não comprova sazonalidade recorrente. Fuso não informado.

## Preparar o ambiente do zero

Pré-requisitos: Git e uv instalado, conforme o preparo da aula 1. Execute na
raiz deste projeto. Python 3.13 é selecionado por `.python-version`; uv pode
obtê-lo se não houver interpretador compatível. `uv.lock` fixa as dependências.

```bash
uv --version
uv sync --locked
uv run python --version
uv run python -c "import duckdb, pandas, streamlit, plotly, pytest, pytest_cov"
```

Não há build-system: segue o formato `uv init --bare` do curso. Stack instalada:
Python 3.13.14, DuckDB 1.5.6, pandas 3.1.0, Streamlit 1.66.1, Plotly 6.9.0,
pytest 9.2.0, pytest-cov 7.1.0 e Ruff 0.17.3. A compatibilidade básica foi
verificada por resolução, instalação e importação, não por execução de pipeline.

## Obter e inspecionar os dados

O script de inspeção usa apenas a biblioteca padrão; não cria banco e não faz
ingestão. O ZIP tem quatro fontes e um dicionário auxiliar.

```bash
mkdir -p data raw
curl -L --fail --max-time 60 'https://www.kaggle.com/api/v1/datasets/download/neethimohan/maven-pizza-challenge-dataset?datasetVersionNumber=1' -o data/pizza-kaggle-v1.zip
uv run python scripts/inspecionar.py data/pizza-kaggle-v1.zip
uv run python -m zipfile -e data/pizza-kaggle-v1.zip raw
```

O SHA-256 esperado do ZIP efetivamente inspecionado é
`a10880d056b5b2f5cd637bd5b435ae3f0f38e76dbc9b0e62fde4313e4a880317`.
Se o conteúdo mudar, investigar em vez de reaproveitar estas contagens como fato.
Nunca salvar os CSVs pelo Excel ou alterar seus bytes.

## Verificações disponíveis agora

```bash
uv run ruff check .
uv run ruff format --check .
```

A inspeção foi repetida, seu JSON comparado byte a byte e os cinco hashes
conferidos com os CSVs extraídos. Evidência em
[docs/evidencias/inspecao.json](docs/evidencias/inspecao.json).

| Fonte | Linhas observadas |
|---|---:|
| orders.csv | 21.350 |
| order_details.csv | 48.620 |
| pizzas.csv | 96 |
| pizza_types.csv | 32 |
| data_dictionary.csv | 15 |

Nas quatro fontes de negócio: zero campos vazios, duplicatas exatas, chaves
primárias repetidas ou FKs órfãs. Datas válidas entre 01/01/2015 e 31/12/2015;
quantidades positivas e preços não negativos. Cinco variantes não têm vendas.
`pizza_types.csv` não é UTF-8 válido; cp1252 é a decodificação proposta.

## Testes e execução do pipeline — etapas futuras

Ainda não existe suíte em `test/`: **testes unitários e cobertura não foram
executados ou medidos**. O comando previsto, após criar os módulos e os testes,
é `uv run pytest --cov`. A meta já configurada é 60%, sobre código Python
relevante, sem incluir a inspeção auxiliar e a interface Streamlit.

Os futuros testes usarão dados sintéticos e DuckDB temporário real, sem tocar
CSV real ou pizza.duckdb. Qualidade sobre os dados reais terá verificações
independentes de PK/FK, tipos, domínios, grãos e reconciliação financeira.

Não executar comandos de ingestão, transformação, marts ou dashboard agora:
os respectivos módulos não existem. O README receberá esses comandos e suas
evidências conforme cada etapa for autorizada e validada. Nenhum resultado
financeiro do pipeline é apresentado nesta entrega.

## Documentos e próximos passos

- [Contrato da Etapa Zero](specs/etapa-zero.md).
- Propostas prévias: [conexão](specs/db.md), [ingestão](specs/ingestao.md),
  [transformação](specs/transformacao.md) e [marts](specs/marts.md).
- [Plano incremental e decisões pendentes](docs/plano.md).
- [Registro de execução](docs/execucao-etapa-zero.md).
- [Instruções para colaboradores e IA](AGENTS.md).

O próximo passo é revisar esta entrega e as hipóteses de negócio. A instrução
do usuário exige essa revisão antes de implementar o pipeline. Primeiro commit
e publicação dependem de autorização. `git status` falhou porque o `.git`
fornecido neste workspace não é um repositório funcional; nenhum commit foi
criado e o histórico não será reconstruído depois.

## Participação da IA

Codex auxiliou na consulta às quatro aulas, verificação da licença, inspeção,
propostas de modelo/specs e preparação do ambiente. Evidências: ZIP identificado
por hash, inspeção de todas as linhas e repetição idêntica do inventário.

Problemas realmente observados: acesso inicial às aulas falhou no navegador e
por DNS no sandbox; curl autorizado permitiu consultá-las. O cache global do uv
era somente leitura no sandbox; acesso autorizado resolveu a verificação e a
instalação. O Ruff encontrou três linhas longas no script proposto pela IA;
elas foram corrigidas e o código formatado antes de nova validação.

Na revisão do usuário, identificou-se outro erro: a primeira entrega usou
specs com seções genéricas e uma tabela de contratos em indicadores.md, em vez
dos formatos ensinados nas aulas. A comparação com os exemplos confirmou a
divergência. As specs foram reorganizadas no formato de contrato/prompt das
aulas, e indicadores.md passou à lista de dez linhas do desafio 1. Os contratos
detalhados foram preservados em documento separado.

Suposições explicitadas para revisão: cp1252 compatível com os bytes não prova
o encoding usado pelo exportador; preço de catálogo não comprova valor histórico
da venda; ranking por tipo agrega tamanhos. O dado ainda não foi ingerido: a
inspeção não prova sucesso de um pipeline inexistente.
# end-to-end-pizza-analytics
