# Contratos analíticos — Pizza Paradise

Status: revisados em 28/10/2026 após validação da refined. Os 13 contratos
estão cobertos por specs/marts.md e implementados em sql/marts/01 a 13.
Resultados: [execução dos marts](execucao-marts.md).
Lista de negócio: [indicadores.md](../indicadores.md).

## População e medidas

Pedido = orders.id único; cliente = customers.id fictício; loja = stores.id.
Item = ocorrência de SKU em order_items, sem identificador natural de linha.
Não eliminar repetições de itens.
Receita por pedido usa total, reconciliado com soma Price de cada ocorrência.
Unidades = nItems, reconciliado com COUNT de ocorrências. Ticket = SUM(total) /
COUNT(pedidos), com uma linha por pedido. Não arredondar antes de reconciliar.
Como a fonte não declara a moeda, a apresentação usa a unidade original,
sem símbolo ou conversão cambial.

Cada mart lê apenas refined e aplica a mesma população: todos os pedidos
válidos, sem filtro de status inexistente. Órfãos, conflitos e falhas de
reconciliação impedem publicação, não autorizam exclusão silenciosa.
Products.SKU é variante; Name consolida tamanhos mediante validação da
consistência da categoria. Preços são de catálogo, sem histórico de vigência;
a coincidência de totais foi demonstrada na versão, não é garantia futura.

## Perguntas, fontes, grãos, fórmulas e aceite

Abreviações: o=orders, i=order_items, p=products, s=stores, c=customers.
Todo nome abaixo corresponde a sql/marts/NN_nome.sql e à tabela marts.nome.

| Arquivo / pergunta | Tabelas e colunas | Grão | Fórmula / inclusão | Aceite |
|---|---|---|---|---|
| 01_vendas_mensais / Como evoluem vendas? | o.id/order_date/total/nItems | Um ano/mês de registro observado | SUM(total), COUNT(id), SUM(nItems) | Totais = KPI; cada pedido em um mês |
| 02_ranking_pizzas / Quais variantes lideram? | i.orderID/SKU; p.SKU/Name/Size/Price; o.id/orderDate | Um SKU com venda | Receita = soma Price por ocorrência; ranking receita | PK SKU; soma receita = total de pedidos |
| 03_pedidos_dia_semana / Quando há mais pedidos? | o.id/order_date | Um dia ISO 1–7 observado | COUNT de pedidos por data de registro | Soma contagens = pedidos; não alegar média diária |
| 04_pedidos_hora / Quais horas concentram pedidos? | o.id/order_timestamp/timestamp_precision | Uma hora de São Paulo conhecida ou grupo sem hora | COUNT por hora_local, timezone America/Sao_Paulo; fuso_horario explícito | Soma incluindo sem hora = pedidos; sem preencher hora ausente |
| 05_ticket_por_pedido / Quanto vale cada venda? | o.id/total; i.orderID/SKU; p.SKU/Price | Um pedido | Total registrado e receita conferida; ticket global no 10 | Soma receita = KPI; uma linha por pedido |
| 06_receita_categoria / Quais categorias lideram? | i.orderID/SKU; p.SKU/Category/Price; o.id/orderDate | Uma categoria com venda | Soma Price por ocorrência | Soma receita = total de pedidos |
| 07_vendas_tamanho / Como vendem tamanhos? | i.orderID/SKU; p.SKU/Size/Price; o.id/orderDate | Um tamanho com venda | COUNT de ocorrências, SUM(Price) | Unidades = nItems; receita = total |
| 08_concentracao_pizzas / Quantos produtos fazem 80%? | i.orderID/SKU; p.SKU/Name/Price; o.id/orderDate | Um Name com venda | Participação e soma acumulada por receita DESC, Name ASC | Último 100%; incluir produto que cruza 80%; prefixo anterior <80% |
| 09_quantidade_por_pedido / Qual a cesta? | o.id/nItems; i.orderID/SKU | Um pedido | nItems e COUNT de ocorrências | Iguais por pedido; soma = KPI |
| 10_kpis / Quais totais e médias? | o.id/total/nItems/orderDate | Uma linha global | SUM(total), COUNT(*), SUM(nItems), média total e nItems | Reconcilia com todas as partições aditivas |
| 11_ranking_tipos_pizza / Quais produtos lideram somando tamanhos? | i.orderID/SKU; p.SKU/Name/Price; o.id/orderDate | Um Name com venda | Soma Price por nome e ranking receita | Cada nome = soma de seus SKUs no 02 |
| 12_vendas_loja / Como cada loja vende? | o.id/storeId/total/nItems/orderDate; s.id/city/state | Uma loja com venda | Receita, pedidos, unidades e ticket por loja | Somas aditivas = KPI; não somar tickets |
| 13_frequencia_clientes / Quantos clientes repetem? | o.id/customerId; c.id | Um número de pedidos por cliente | Agregar pedidos por cliente e depois distribuir; percentual de clientes e recompra prontos no SQL | Soma clientes = distintos com compra; soma frequência × clientes = pedidos |

Não somar clientes distintos entre lojas ou períodos como se fossem exclusivos.
Clientes sem compra ficam fora do denominador de recompra. Dados representam
2020–2022; não classificar cliente como perdido por não aparecer depois.
Nenhum mart consulta os demais: reconciliações são verificações independentes.

## Fuso, empates e percentuais

Data sem horário mantém sua data, mas não recebe meia-noite inventada.
Horários originais permanecem UTC na refined; o mart horário usa
America/Sao_Paulo por decisão de 29/10/2026. Não é o fuso comercial das lojas.
Meses/dias continuam pela data da fonte; somente o agrupamento horário muda.
Filtro de período e
regras de fuso devem ser iguais em todos os indicadores comparados.
Ranking usa DENSE_RANK, com mesma posição em empate; ordenação visual usa
SKU/Name estável sem alterar a posição.
Pareto usa janela ROWS e desempate estável, comparando valores sem arredondar.
Resumo do grupo de 80% é calculado em SQL; medidas globais repetidas em linhas
não são aditivas. Receita zero impede o Pareto até definição explícita.
O grupo inclui linhas cuja receita acumulada anterior × 100 é menor que
receita total × 80. Comparar valores exatos, sem arredondar o percentual.
Frequência entrega clientes por quantidade de pedidos, participação desses
clientes e proporção global com mais de um pedido. A proporção global repetida
por faixa não pode ser somada.

Usar order_date nas partições temporais e timezone('America/Sao_Paulo',
order_timestamp) nas horas;
orderDate preservada serve como rastreabilidade, não exige novo parsing.
Todos os marts usam a janela inteira observada. Grãos globais não suportam
filtros arbitrários de período no dashboard sem revisar esse contrato.
Comparar somas monetárias exatamente; razões por numerador/denominador com
tolerância absoluta de 1e-9. Não aplicar essa tolerância às receitas.

## Validações concluídas e limites

Refined validada, regras monetárias e temporais aprovadas e implementadas.
Consulta somente leitura de 28/10/2026 confirmou zero Name com categorias
conflitantes; o executor deve verificar novamente antes de cada publicação.
Treze marts publicados e auditados após a revisão. Moeda declarada e fuso comercial local
não são inferidos: calcular na unidade original e exibir horas de São Paulo
como referência escolhida, sem afirmar USD comprovado ou horário comercial.
Não há necessidade de conversão cambial.
