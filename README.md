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
Na refined, IDs serão texto e dinheiro DECIMAL. Repetições de itens representam
unidades e precisam permanecer. Há datas com/sem segundos e apenas data:
não inventar meia-noite para os 116 registros sem hora.
[Modelo completo](docs/modelo.md) e [transformação proposta](specs/transformacao.md).

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
uv run python scripts/baixar_paradise.py
uv run python -m pipeline.ingestao --banco data/pizza-paradise-validacao.duckdb
uv run python -m pipeline.ingestao
uv run python scripts/auditar_paradise.py
```

O segundo comando é uma carga opcional de ensaio em arquivo separado. O terceiro
recria RAW no banco principal e o quarto compara cada valor e multiplicidade
com a fonte, verifica tipos e FKs. Não executar com a UI aberta. A aquisição
precisa de rede na primeira execução; se as fontes já existem, confere hashes
sem baixá-las novamente. Conteúdo local divergente não é sobrescrito.

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
projeto. Suíte migrada: 26 testes passaram, cobertura total 98,71% das 155 linhas
executáveis, acima da meta de 60%. Inclui aquisição gzip/hashes, CSV e Parquet
reais sintéticos, repetições preservadas, mudança de esquema e rollback após
erro real em páginas Parquet. Evidência: [registro da migração](docs/migracao-pizza-paradise.md).

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

## Desenvolvimento e participação da IA

Specs anteriores ao código em specs/; um SQL por indicador em sql/marts/
quando implementados. [Metodologia](docs/metodologia.md) e histórico de commits
mantêm a evolução real, sem reconstrução posterior.
Transformação, marts e dashboard não foram implementados nesta migração.

Codex auxiliou inspeção, specs, implementação anterior e testes. Problemas reais
estão nos registros: acesso DNS/cache, formatação, bloqueio pela UI e correção
do formato das specs após revisão do usuário. Na nova fonte, a auditoria
identificou compressão gzip nos CSVs, variações de data e repetições legítimas
de itens; essas evidências mudaram o contrato antes do código.
A hipótese de preço e as regras Maven não foram transferidas automaticamente.

Registros históricos: [Etapa Zero](docs/execucao-etapa-zero.md),
[conexão](docs/execucao-db.md), [ingestão Maven](docs/execucao-ingestao.md) e
[UI](docs/execucao-ui.md). Eles descrevem suas versões, não resultados da fonte
nova. Arquivos de dados, banco e instruções locais ficam fora do Git.
