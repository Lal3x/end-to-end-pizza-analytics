# Pizza Paradise — pipeline analítico local

Fonte ativa: Pizza Paradise, dados fictícios da Observable, notebook versão 398.
Migração da ingestão Maven concluída e validada; ver [plano](docs/plano.md) e
[registro da migração](docs/migracao-pizza-paradise.md).
A versão anterior permanece no histórico e suas fontes locais são preservadas.

## Objetivo e fonte

Analisar vendas por produto/tamanho, período, loja e frequência de clientes,
com qualidade verificável e SQL rastreável.
Fonte: [Pizza Paradise](https://observablehq.com/@observablehq/pizza-paradise-data),
gerado pela equipe Observable; notebook de Paul Buffa.
A fonte permite uso amplo no texto, mas não declara licença padronizada nos
metadados dos anexos. Não publicar os arquivos completos sem esclarecer termos.
Detalhes e atribuição: [fonte e permissão](docs/fontes-e-licenca.md).

Na inspeção: 2.046.713 pedidos, 2.916.015 ocorrências de itens, 34.761 clientes,
32 lojas e 36 SKUs; período 2020–2022. São dados sintéticos, não vendas de uma
empresa real. [Avaliação](docs/avaliacao-pizza-paradise.md) e
[evidência](docs/evidencias/pizza-paradise-inspecao.json).

## Modelo e arquitetura

A organização das etapas foi corrigida após revisão do usuário:

```text
pipeline/
  ingestao.py
  transformacao.py   transformação com pandas
  marts.py           execução dos SQLs e auditorias
db.py                conexão compartilhada, na raiz
baixar_dados.py      preparação das fontes, independente
ui.py                exploração local
sql/marts/           13 SQLs dos indicadores
sql/validar_*.sql    auditorias de entrada e saída dos marts
```

`pipeline/` não contém aquisição, configuração de fontes ou executor de
transformação SQL. As três etapas e o dashboard Streamlit estão implementados.

| Tabela | Grão / PK | Relacionamentos |
|---|---|---|
| orders | Um pedido / id | customerId → customers.id; storeId → stores.id |
| order_items | Uma ocorrência de item / sem PK natural de linha | orderID → orders.id; SKU → products.SKU |
| products | Uma variante / SKU | Nome e tamanho no catálogo |
| customers | Um cliente fictício / id | Coordenadas |
| stores | Uma loja / id | Localização |

```text
Anexos oficiais CSV/Parquet → raw/pizza_paradise/
  → pizza.duckdb: raw.* → refined.* → marts.* → dashboard
```

RAW preserva CSV em texto e Parquet nos tipos nativos, sem deduplicação.
Na refined, IDs são texto e dinheiro DECIMAL(18,2). Repetições de itens representam
unidades e precisam permanecer. Há datas com/sem segundos e apenas data:
não inventar meia-noite para os 116 registros sem hora.
[Modelo completo](docs/modelo.md) e [contrato da transformação](specs/transformacao.md).

## Ambiente

Python 3.13 e uv. Sem Docker, Spark, nuvem ou outro banco.

```bash
uv sync --locked
uv run python --version
uv run python -c "import duckdb, pandas, streamlit, plotly"
```

## Aquisição e ingestão — incremento da migração

Aquisição e ingestão implementadas. Execute na raiz do projeto:

```bash
uv run python baixar_dados.py
uv run python -m pipeline.ingestao --banco data/pizza-paradise-validacao.duckdb
uv run python -m pipeline.ingestao
uv run python scripts/auditar_paradise.py
```

O segundo comando é uma carga opcional de ensaio em arquivo separado. O terceiro
recria RAW no banco principal e o quarto compara cada valor e multiplicidade
com a fonte, verifica tipos e FKs. Não executar com a UI aberta. A aquisição
precisa de rede na primeira execução; se as fontes já existem, confere hashes
sem baixá-las novamente. Conteúdo local divergente não é sobrescrito.
Após publicar refined, a ingestão bloqueia sua recriação para evitar trocar
RAW mantendo camadas derivadas antigas. Para uma nova carga, usar banco separado
e revisar a atualização das camadas.

Nesta migração, o banco antigo foi preservado em
data/backups/maven-e8542a701d7a.duckdb, com SHA-256 e contagens registrados em
[backup-maven.json](docs/evidencias/backup-maven.json). Os CSVs antigos também
permanecem locais. Para outra instalação com banco de fonte anterior, preservar
uma cópia com a UI encerrada antes de executar a nova carga.

### Resultados verificados

| Tabela RAW | Linhas |
|---|---:|
| orders | 2.046.713 |
| order_items | 2.916.015 |
| customers | 34.761 |
| stores | 32 |
| products | 36 |
| Total | 4.997.557 |

Aquisição validada por hashes; ensaio e reexecução com mesmo resultado de
auditoria; carga final idêntica ao ensaio. Zero diferenças de valores ou
multiplicidade por EXCEPT ALL; quatro FKs sem órfãos. As repetições de itens
permanecem. CSVs ficaram VARCHAR; Parquets mantiveram tipos nativos.
No ensaio medido nesta máquina: 2,59 s e pico de memória residente 588.552 KiB
(cerca de 575 MiB), sem swap. É uma medição da ingestão, não promessa para
outra máquina nem medição da futura transformação.

## Transformação com pandas

Com RAW carregada e a UI encerrada:

```bash
uv run python -m pipeline.transformacao
```

Converte uma tabela por vez, preserva RAW e publica refined em transação única.
O JSON de saída relata nulos, tipos, contagens, duplicatas, correções de Launch,
precisão temporal, reconciliações, tempo e pico RSS do processo. Para ensaio,
use `--banco caminho/do/banco.duckdb` em uma cópia com RAW já carregada.
Falhas restauram refined anterior. A reexecução substitui a camada.
Horários com Z permanecem UTC; datas sem hora têm timestamp nulo.
As funções principais documentam parâmetros, retorno e falhas em docstrings.

## Marts dos indicadores

Com refined publicada e a UI encerrada:

```bash
uv run python -m pipeline.marts
```

Executa os 13 arquivos de sql/marts em ordem e publica marts em transação única.
Auditorias SQL conferem fontes, grãos, quantidades, receitas, rankings, Pareto
e frequência de clientes; qualquer falha preserva a camada anterior. Reexecução
substitui a camada e remove tabelas antigas extras. `--banco caminho.duckdb`
permite ensaio em cópia existente com refined carregada.

Os valores usam a unidade monetária da fonte; horas são exibidas em
America/Sao_Paulo (UTC−03:00 em 2020–2022). Timestamps da refined continuam UTC;
meses e dias mantêm a data original. São Paulo é referência de visualização,
não o fuso comercial das lojas americanas. Os marts
representam a janela completa: filtros arbitrários de data no dashboard exigem
revisão dos grãos e denominadores. Resultados e limitações:
[execução dos marts](docs/execucao-marts.md).

## Exploração e testes

```bash
uv run python ui.py
uv run pytest --cov
uv run ruff check .
uv run ruff format --check .
```

A UI abre http://localhost:4213; Ctrl+C encerra e libera o banco.
As consultas dependem da fonte realmente carregada. Após a migração:
```sql
SELECT * FROM raw.orders LIMIT 10;
SELECT * FROM raw.order_items LIMIT 10;
```

Testes usam fontes sintéticas e DuckDB temporário real, sem rede ou banco do
projeto. Com apresentação: 112 testes passaram, cobertura total 94,05% das 521 linhas
executáveis, acima da meta de 60%. Inclui aquisição gzip/hashes, CSV e Parquet
reais sintéticos, repetições preservadas, mudança de esquema e rollback após
erro real em páginas Parquet. Evidência: [registro da migração](docs/migracao-pizza-paradise.md).
Transformação: datas inválidas, precisão temporal, centavos, domínios, conflitos,
FKs, reconciliação, idempotência e rollback com refined anterior preservada.
O teste de regressão monetária inclui valor maior depois da amostra inicial.
Resultados reais: [execução da transformação](docs/execucao-transformacao.md).

## Indicadores, fórmulas e limites

[Treze candidatos](indicadores.md) e [contratos](docs/contratos-indicadores.md):
vendas mensais, ranking SKU, dia/hora, ticket, categoria, tamanho, Pareto, cesta,
KPIs, ranking consolidado, lojas e frequência de clientes.
Receita por pedido = total, conferido contra soma Price por ocorrência;
unidades = nItems, conferido contra COUNT de itens. Ticket parte de pedido,
nunca da média de preços ou da média de médias. Não somar total após JOIN 1:N.

Moeda precisa ser formalizada para esta fonte; USD ainda é proposta pelo
contexto americano, não declaração explícita nos anexos. Sem custos, status,
pagamentos ou eventos logísticos, não afirmar lucro, cancelamento ou atraso.

## Dashboard Streamlit

Com os marts publicados e a UI DuckDB encerrada:

```bash
uv run streamlit run app.py
```

Abrir http://localhost:8501. O painel tem sete gráficos Plotly, quatro KPIs
principais e três auxiliares, com fundo ciano claro. `painel.py` lê/formata/desenha;
`app.py` organiza a interface e o cache. Leituras somente em marts, com conexão
read_only fechada após a consulta. **Recarregar dados** atualiza o cache depois
de executar os marts. Seleções mensais e ranking por SKU/Name não alteram KPIs.

Banco ou fonte ausente gera erro claro com orientação. Nenhum indicador é
calculado na apresentação. [Execução e validação](docs/execucao-dashboard.md),
[captura desktop](docs/evidencias/dashboard-desktop.png) e
[captura móvel](docs/evidencias/dashboard-mobile.png).

## Desenho do dashboard

[Rascunho HTML](design/rascunho.html) com dados reais dos marts agregados,
[PNG desktop](design/rascunho.png) e [PNG móvel](design/rascunho-mobile.png).
Para abrir o HTML, manter design/dados.js ao lado dele. Atualizar o retrato:

```bash
uv run python scripts/preparar_rascunho.py
```

O protótipo tem fundo ciano claro, cartões com valores completos, sete gráficos
com mart de origem e frases-resposta. O PNG é captura real do HTML renderizado.
Validações e comandos de captura: [registro do rascunho](docs/execucao-rascunho.md).
O HTML é o desenho preservado; a aplicação funcional está em app.py/painel.py.
Pareto mostra nomes dos produtos no eixo X; horas usam America/Sao_Paulo.
Revisão do formato das specs e verificações: [registro](docs/validacao-specs-e-fuso.md).

## Desenvolvimento e participação da IA

Specs anteriores ao código em specs/; um SQL por indicador em sql/marts/
quando implementados. [Metodologia](docs/metodologia.md) e histórico de commits
mantêm a evolução real, sem reconstrução posterior.
A investigação SQL anterior permanece como [registro histórico](docs/validacao-refined.md),
mas seus arquivos e testes saíram do fluxo ativo: ela não implementa a nova
transformação com pandas. O dashboard Streamlit já está implementado.

Eu ampliei a estrutura com módulos de aquisição/configuração dentro de pipeline
e preparei transformação por SQL, contrariando a organização solicitada pelo
usuário. A correção remove esses módulos da pasta de etapas e estabelece
transformacao.py com pandas. As regras de qualidade dos dados permanecem;
não foram criados arquivos vazios para aparentar etapas prontas.

Codex auxiliou inspeção, specs, implementação anterior e testes. Problemas reais
estão nos registros: acesso DNS/cache, formatação, bloqueio pela UI e correção
do formato das specs após revisão do usuário. Na nova fonte, a auditoria
identificou compressão gzip nos CSVs, variações de data e repetições legítimas
de itens; essas evidências mudaram o contrato antes do código.
A hipótese de preço e as regras Maven não foram transferidas automaticamente.

Registros históricos: [Etapa Zero](docs/execucao-etapa-zero.md),
[conexão](docs/execucao-db.md), [ingestão Maven](docs/execucao-ingestao.md) e
[UI](docs/execucao-ui.md). Eles descrevem suas versões, não resultados da fonte
nova. Fontes brutas, banco e instruções locais ficam fora do Git. O retrato
agregado do desenho e suas imagens são artefatos de revisão do dashboard.
