# Execução dos marts — Pizza Paradise

Data: 28/10/2026. Contrato: [spec](../specs/marts.md).
Revisão de 29/10/2026: mart horário em America/Sao_Paulo, preservando os
timestamps UTC da refined. As medições abaixo são da carga original; o código
atual incorpora a conversão de fuso solicitada pelo usuário.
Executor: [pipeline/marts.py](../pipeline/marts.py). Um SELECT numerado por
indicador em sql/marts, consultando somente refined. Nenhuma fórmula de negócio
em Python. Docstrings explicam execução, parâmetros, erros e transação.

## Execução real

Ensaio em cópia existente do banco, reexecução nessa cópia e publicação no banco
principal. Comandos equivalentes na raiz:

```bash
uv run python -m pipeline.marts --banco caminho/da/copia.duckdb
uv run python -m pipeline.marts
```

Nesta sessão foi usado .venv/bin/python do ambiente já instalado, sem baixar
dependências. Ensaio: 3,573 s; reexecução: 3,487 s; carga principal: 3,460 s.
Tempos medidos nesta máquina, sem garantia de desempenho em outro ambiente.
A suíte de testes rodou em paralelo à carga principal; não é benchmark isolado.

| Mart | Linhas |
|---|---:|
| vendas_mensais | 36 |
| ranking_pizzas | 36 |
| pedidos_dia_semana | 7 |
| pedidos_hora | 20 |
| ticket_por_pedido | 2.046.713 |
| receita_categoria | 3 |
| vendas_tamanho | 4 |
| concentracao_pizzas | 9 |
| quantidade_por_pedido | 2.046.713 |
| kpis | 1 |
| ranking_tipos_pizza | 9 |
| vendas_loja | 32 |
| frequencia_clientes | 990 |

As 20 linhas de hora incluem as horas observadas e o grupo sem hora. Não se
trata de uma grade com todas as 24 horas. As 990 linhas de frequência são
faixas observadas de quantidade de pedidos por cliente, não total de clientes.
Não somar contagens entre marts de grãos diferentes.

## Auditorias e preservação

sql/validar_refined.sql confere PKs, FKs, medidas, precisão temporal,
Name/Category e reconciliação de itens por pedido, antes do DROP de marts.
sql/validar_marts.sql confere grãos, partições, valores exatos, ticket, posição
nos rankings, ordem e corte de Pareto e denominadores da frequência de clientes.
Qualquer linha retornada por uma auditoria impede commit.

Primeira carga e reexecução foram comparadas com EXCEPT ALL nos dois sentidos;
o mesmo foi feito entre carga principal e ensaio reexecutado. RAW e refined
foram comparadas com a cópia anterior, por valores, multiplicidades, colunas
e tipos. Resultados em [evidência JSON](evidencias/marts-pizza-paradise.json).

Não se deduplicam itens. Pedidos com vários itens contam uma vez no ticket.
Empates têm DENSE_RANK igual; Pareto desempata por Name e inclui a linha que
atinge ou cruza 80%. Receita zero falha. Clientes/lojas sem compra não entram
nos denominadores. Ausência de recompra produz proporção zero, não NULL.

## Testes e problemas encontrados

86 testes passaram em 11,04 s, cobertura total 92,42% de 409 linhas executáveis;
25 testes novos dos marts. Ruff check e format check aprovados.
Cobertura usa somente exemplos sintéticos e DuckDB temporário real, sem rede
ou banco do projeto. Inclui reexecução, remoção de tabela obsoleta, arquivos
ausentes/inesperados, SQL inválido, mart vazio, valores errados, refined
inconsistente e preservação dos marts anteriores após falha.

Na preparação, get_table_names do DuckDB falhou em JOIN USING durante a inspeção
das fontes e devolveu aliases junto aos nomes qualificados. Os SELECTs passaram
a usar ON explícito e a inspeção remove somente o alias retornado pela API.
Um arquivo chamado marts.duckdb também mostrou ambiguidade entre catálogo e
schema. O executor anexa o arquivo com alias fixo em uma conexão em memória,
sem carregar os dados em DataFrames; um teste cobre esse nome de arquivo.

Código, SQL e documentação foram editados por patches; Ruff format ajustou
layout Python. O JSON é artefato gerado das execuções e comparações reais.
Nenhum commit ou publicação externa foi realizado.

## Limites e próximo passo

Moeda declarada e fuso comercial local continuam sem comprovação na fonte.
Usar valores originais e UTC; não rotular USD como fato confirmado. Os marts
representam toda a janela observada. Filtros arbitrários de período exigem
revisar os grãos, principalmente rankings, Pareto e frequência.
Dashboard ainda não implementado; próximo passo é seu rascunho e contrato.
