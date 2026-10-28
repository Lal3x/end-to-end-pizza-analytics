# Indicadores de desempenho comercial da pizzaria

Objetivo: acompanhar o desempenho das vendas, a composição do portfólio vendido
e a distribuição temporal dos pedidos, com definições rastreáveis aos dados.

Status: proposta para revisão, baseada nos CSVs inspecionados. Os indicadores
ainda não foram calculados pelo pipeline. Formato: **indicador — tabelas
(colunas) — o que mede**. O marcador `?` identifica indicadores dependentes da
hipótese de preço de catálogo: seu uso em USD foi aprovado, mas a limitação
histórica permanece. Após a validação conjunta, o usuário autorizou avançar
com esta seleção e suas definições, mantendo a implementação por etapas.

1. **Evolução mensal das vendas (?)** — orders (order_id, date) + order_details (order_id, pizza_id, quantity) + pizzas (pizza_id, price) — acompanha receita estimada, pedidos e unidades vendidas por mês de registro, permitindo comparar o desempenho ao longo do período observado.
2. **Ranking de variantes de pizza por receita estimada (?)** — order_details (pizza_id, quantity) + pizzas (pizza_id, pizza_type_id, size, price) + pizza_types (pizza_type_id, name) — ordena cada combinação de tipo e tamanho pela receita estimada, distinguindo, por exemplo, Havaiana M de Havaiana L.
3. **Distribuição de pedidos por dia da semana** — orders (order_id, date) — apresenta o total de pedidos registrados em cada dia da semana para identificar a concentração semanal das vendas.
4. **Distribuição de pedidos por hora do dia** — orders (order_id, time) — apresenta o total de pedidos registrados em cada faixa de uma hora para identificar os horários de maior volume de pedidos.
5. **Ticket médio estimado por pedido (?)** — orders (order_id) + order_details (order_id, pizza_id, quantity) + pizzas (pizza_id, price) — mede a receita média estimada de um pedido, calculada após consolidar todos os seus itens, para acompanhar o valor médio das vendas.
6. **Receita estimada por categoria (?)** — order_details (pizza_id, quantity) + pizzas (pizza_id, pizza_type_id, price) + pizza_types (pizza_type_id, category) — compara a receita estimada das categorias do cardápio para avaliar sua contribuição ao resultado comercial.
7. **Composição das vendas por tamanho (?)** — order_details (pizza_id, quantity) + pizzas (pizza_id, size, price) — compara unidades vendidas e receita estimada entre tamanhos, distinguindo participação em volume de contribuição em valor.
8. **Pareto da receita estimada por tipo de pizza (?)** — order_details (pizza_id, quantity) + pizzas (pizza_id, pizza_type_id, price) + pizza_types (pizza_type_id, name) — identifica quantos tipos de pizza, e qual percentual dos tipos com vendas, são necessários para alcançar pelo menos 80% da receita estimada, ordenando os produtos por receita decrescente.
9. **Volume de pizzas por pedido** — orders (order_id) + order_details (order_id, quantity) — apresenta o total de unidades de pizza em cada pedido para caracterizar o tamanho das cestas, sem confundir quantidade de pizzas com quantidade de linhas de item.
10. **Resumo executivo de vendas (?)** — orders (order_id, date) + order_details (order_id, pizza_id, quantity) + pizzas (pizza_id, price) — reúne receita estimada, total de pedidos, unidades vendidas e ticket médio estimado no período completo, oferecendo uma visão consolidada dos indicadores detalhados.
11. **Ranking consolidado de tipos de pizza por receita estimada (?)** — order_details (pizza_id, quantity) + pizzas (pizza_id, pizza_type_id, price) + pizza_types (pizza_type_id, name) — ordena os tipos de pizza somando a receita de todos os seus tamanhos, para comparar a contribuição de cada produto independentemente da variante.

## Convenções de leitura

- **Receita estimada:** quantidade vendida multiplicada pelo preço de catálogo,
  expressa em USD. Não representa lucro nem recebimento financeiro comprovado.
- **Pedido:** um identificador distinto de pedido; não equivale a cliente único.
- **Unidade vendida:** uma pizza contabilizada em `quantity`; uma linha pode
  representar mais de uma unidade.
- **Tipo de pizza:** produto identificado por `pizza_type_id`, agregando tamanhos.
  **Variante:** combinação comercial identificada por `pizza_id`.
- **Período da venda:** data de registro do pedido em `orders.date`. O horário
  vem de `orders.time`, sem fuso informado.

O resumo executivo consolida medidas da lista; não é um indicador independente
adicional. Distribuições por dia da semana e hora mostram totais observados,
sem normalização por dias de funcionamento. Um único ano permite descrever
variações mensais, mas não comprovar sazonalidade recorrente.

O Pareto detalha a concentração da receita: apresenta a receita de cada tipo,
sua participação e o percentual acumulado. O grupo que alcança 80% inclui o
produto que cruza esse limite. A proporção de produtos será calculada sobre os
tipos com vendas no mesmo período; não se presume que 20% dos tipos respondam
por 80% da receita. Empates são ordenados pelo identificador do tipo de pizza
para garantir resultado reproduzível.

## Hipótese aprovada e condições de cálculo

Os indicadores com `?` têm as colunas necessárias e usam a hipótese aprovada de
que `pizzas.price` é aplicável às vendas registradas. O dicionário informa USD;
não há preço no item nem histórico para comprovar o preço praticado. Contagens
e quantidades não dependem dessa hipótese. O `?` não significa coluna ausente.

Os indicadores temporais também dependem da conversão explícita das datas e
horas de texto. Nove dos onze candidatos cruzam duas tabelas ou mais. As regras
de inclusão e o período devem ser iguais nas comparações entre indicadores.

## O que o dado não sustenta

- Lucro e margem: não há custos, despesas ou impostos.
- Clientes únicos e recompra: não há identificador de cliente.
- Cancelamento: não existe status do pedido.
- Estoque: não há saldos, movimentações ou ficha técnica de consumo.
- Tempo de preparo ou entrega: existe apenas data/hora de registro do pedido.
- Efeito de promoções: não há campanhas identificadas nem grupo de comparação.

As definições de pedido, item, receita, período, classificação e população,
assim como os contratos propostos para cada mart, estão em
[docs/contratos-indicadores.md](docs/contratos-indicadores.md). A seleção e os
contratos dos marts foram validados para avançar; alterações futuras devem ser
documentadas antes da implementação correspondente.

## Validação técnica e de negócio dos candidatos

Os onze candidatos são viáveis com as colunas existentes e com a hipótese de
preço aprovada. Esta é uma validação de definições e fontes, não de resultados
de marts: nenhum SQL de indicador foi implementado ou executado.

| Candidato | Parecer | Condição de interpretação |
|---|---|---|
| 1. Evolução mensal | Faz sentido para acompanhar a trajetória das vendas | Comparar totais mensais; meses têm durações diferentes e um ano não comprova sazonalidade recorrente |
| 2. Ranking por variante | Faz sentido e foi escolhido pelo usuário | Grão pizza_id; exibir nome e tamanho; receita não equivale a popularidade em unidades |
| 3. Pedidos por dia da semana | Faz sentido como distribuição observada | Não é média por dia aberto; o calendário e os dias sem registro afetam a comparação |
| 4. Pedidos por hora | Faz sentido para identificar concentração de registros | Não mede ocupação, fila, capacidade ou tempo de preparo |
| 5. Ticket médio | Faz sentido para medir valor médio de pedido | Consolidar receita por pedido antes da média; resultado global no mart 10, detalhe auditável no 05 |
| 6. Receita por categoria | Faz sentido para avaliar composição das vendas | Categorias devem particionar a receita; não somar pedidos entre categorias como se fossem exclusivos |
| 7. Vendas por tamanho | Faz sentido para comparar volume e valor | Unidades e receita são medidas distintas; tamanho maior pode gerar mais receita com menos unidades |
| 8. Pareto por tipo | Faz sentido para medir concentração do portfólio | Manter grão tipo nesta proposta, incluir quem cruza 80% e não presumir que o grupo será 20% dos tipos |
| 9. Volume por pedido | Faz sentido para caracterizar as cestas | Somar quantity; a saída por pedido é detalhe analítico, não uma média já calculada |
| 10. Resumo executivo | Faz sentido como consolidação | Reutiliza conceitos dos demais indicadores; não constitui uma medida nova independente |
| 11. Ranking consolidado | Faz sentido e complementa a visão por variante | Grão pizza_type_id; não somar valores dos dois rankings entre si, pois representam as mesmas vendas |

A conferência somente leitura dos CSVs encontrou 91 variantes com vendas e
32 tipos com vendas; 29 tipos venderam em mais de um tamanho. As chaves usadas
nas relações são únicas, todos os itens encontram pedido e variante, todas as
variantes encontram tipo e nenhum pedido está sem item. Isso sustenta as duas
visões de ranking sem criar entidades ou relações artificiais. As contagens
descrevem a fonte atual, não metas fixas para futuras atualizações.

Após este parecer, o usuário autorizou avançar com a seleção completa e o
Pareto por tipo. Isso aprova as definições, não antecipa validação dos futuros
resultados nem autoriza publicação ou commits.
