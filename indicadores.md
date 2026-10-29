# Indicadores de desempenho — Pizza Paradise

Fonte: dados fictícios de pedidos, itens, produtos, clientes e lojas da Observable.
Contratos revisados após validar refined em 28/10/2026.
Formato: indicador — tabelas (colunas) — o que mede.
Treze marts calculados e validados pelo pipeline; resultados em
[execução dos marts](docs/execucao-marts.md).

1. **Evolução mensal das vendas** — orders (id, orderDate, total, nItems) — acompanha receita registrada, pedidos e unidades por mês, permitindo comparações entre 2020 e 2022.
2. **Ranking de variantes por receita** — order_items (orderID, SKU) + products (SKU, Name, Size, Price) + orders (id, orderDate) — compara cada SKU separadamente, identificando produto e tamanho.
3. **Pedidos por dia da semana** — orders (id, orderDate) — apresenta a distribuição dos pedidos por dia de registro, sem confundir totais com média por dia aberto.
4. **Pedidos por hora** — orders (id, orderDate) — mostra horários dos registros com hora conhecida e uma categoria separada para os pedidos cuja fonte só informa a data.
5. **Ticket médio por pedido** — orders (id, total) — mede a média do total no grão original de pedido; o total é reconciliado com os itens antes de publicar.
6. **Receita por categoria** — order_items (orderID, SKU) + products (SKU, Category, Price) + orders (id, orderDate) — compara a receita dos itens entre categorias do catálogo.
7. **Vendas por tamanho** — order_items (orderID, SKU) + products (SKU, Size, Price) + orders (id, orderDate) — compara unidades e receita por tamanho, contando cada ocorrência de item.
8. **Pareto por produto consolidado** — order_items (orderID, SKU) + products (SKU, Name, Price) + orders (id, orderDate) — identifica quantos nomes de produto com vendas alcançam pelo menos 80% da receita, incluindo o produto que cruza o limite.
9. **Volume de pizzas por pedido** — orders (id, nItems) + order_items (orderID, SKU) — caracteriza a cesta por pedido e confere a quantidade registrada com o número de ocorrências de itens.
10. **Resumo executivo** — orders (id, orderDate, total, nItems) — reúne receita, pedidos, unidades, ticket médio e média de unidades por pedido, sem média de médias.
11. **Ranking consolidado por produto** — order_items (orderID, SKU) + products (SKU, Name, Price) + orders (id, orderDate) — agrega tamanhos por Name para comparar produtos, após validar a consistência de nome/categoria.
12. **Desempenho por loja** — orders (id, storeId, total, nItems, orderDate) + stores (id, city, state) — compara pedidos, unidades, receita e ticket por loja no mesmo período.
13. **Frequência de compra por cliente** — orders (id, customerId) + customers (id) — distribui clientes com compras por quantidade de pedidos e calcula a proporção com mais de um pedido no período observado.

## Regras de interpretação

Cada linha de order_items representa uma ocorrência vendida, mesmo que o par
(orderID, SKU) se repita. Não deduplicar; não existe quantity nessa fonte.
Receita de item = Price por ocorrência. Receita do pedido = total, validado
contra soma de itens em centavos. Não somar total após JOIN com itens.

SKU identifica variante; Name é agrupamento consolidado, não PK de produto.
Os rankings representam as mesmas vendas e seus totais não devem ser somados
entre si. Pareto é mantido consolidado por Name; empates usam ordem estável,
sem presumir relação 80/20.

orderDate tem valores com Z (UTC) e valores apenas com data. O período de
registro será definido pela representação da fonte, sem assumir fuso local
da loja. Pedidos sem hora permanecem na contagem e são marcados como hora
não informada no mart horário. Datas e instantes UTC continuam na refined.
Revisão de 29/10/2026: o mart horário usa America/Sao_Paulo, como referência
comum de visualização. Mês/dia da semana permanecem pela data original da fonte.

A moeda USD é uma proposta de apresentação coerente com o contexto das lojas,
mas não foi identificada declaração explícita nos anexos. Não converter moeda
nem rotular valores como USD comprovado sem resolver essa pendência.
Recompra é frequência observada em dados fictícios; não retenção de uma empresa
real, e início/fim da janela limitam a interpretação.

## O que o dado não sustenta

Lucro/margem (sem custos), cancelamento (sem status), pagamentos (sem transações),
prazo/preparo/entrega (sem eventos logísticos), estoque (sem saldos) e efeito
causal de campanhas (sem tratamento/controle). Coordenadas não são rotas.
Não inferir demografia de clientes a partir de ID e posição.

Contratos e critérios: [docs/contratos-indicadores.md](docs/contratos-indicadores.md).
