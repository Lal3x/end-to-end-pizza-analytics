# Contratos analíticos propostos

Status: definições validadas pelo usuário para avançar por etapas. Nenhum mart
implementado; resultados dependerão de execução, testes e reconciliações.

Detalhamento dos candidatos listados em [indicadores.md](../indicadores.md).
Aqui ficam as definições e contratos para a revisão dos marts. A lista da
aula 1 permanece na raiz, com uma linha por indicador.

Pedido é um `orders.order_id` registrado por uma mesa, conforme dicionário;
não identifica pessoa ou cliente único. Item é uma linha `order_details_id`,
que pode representar várias pizzas iguais via `quantity`. Pizza física vendida
é uma unidade de quantity; não é uma linha de item.

Receita estimada em USD = SUM(quantity × pizzas.price). O dicionário declara
price em USD, mas a base não guarda preço transacional, descontos, impostos,
pagamentos nem histórico de vigência. Usar o preço do catálogo para 2015 é uma
hipótese explicitamente aprovada pelo usuário; não há como verificar o preço
efetivo em cada venda. A seleção e as definições dos indicadores foram
validadas em conjunto antes da autorização para avançar.
Essa medida não comprova caixa recebido nem lucro.

A data de registro `orders.date` define o período e o dia da semana. O horário
é `orders.time`, sem fuso conhecido. Não representa entrega, preparo ou duração.
Ticket médio = média da receita dos pedidos, após uma linha por order_id;
equivale a receita total / pedidos incluídos. Não calcular média de preços,
média dos tickets mensais ou soma de tickets.

Ranking principal (02): uma variante por `pizza_id`, com nome do tipo e tamanho
separados, conforme decisão do usuário. Ranking consolidado adicional (11):
um tipo por `pizza_type_id`, agregando tamanhos. O Pareto (08) permanece por
tipo nesta proposta. Tamanho vem de pizzas.size; categoria de
pizza_types.category. Não extrair tamanho por sufixo do ID. Empates de receita
recebem o mesmo rank; ordenação visual usa o ID do respectivo grão como
desempate. Curvas acumuladas por tipo usam pizza_type_id.

População proposta: todos os pedidos e seus itens, sem filtro de status (coluna
inexistente), com PK/FK, tipos e domínios válidos. Inválidos interrompem a etapa;
não são descartados silenciosamente. No cenário atual todo pedido tem item.
Pedido futuro sem item será anomalia impeditiva até decisão explícita; não
inventar ticket zero. Produtos sem vendas ficam fora de rankings de venda;
catálogo completo pode aparecer separadamente se uma pergunta futura exigir.

## Perguntas candidatas e contratos analíticos

Rastreabilidade do ticket: o mart 05 propõe uma linha de receita por pedido,
permitindo auditar o valor de cada venda. O ticket médio global será entregue
pronto pelo mart 10, calculado diretamente de refined com a mesma consolidação
por pedido. O mart 10 não lê o mart 05; as duas saídas serão reconciliadas.
Essa divisão mantém o ticket rastreável e sem cálculo na apresentação.

Todos os SQLs futuros lerão apenas refined. Todos usam a população acima. Nos
critérios, “total” é a mesma população, com DECIMAL e sem arredondamento precoce.
`o` = orders, `d` = order_details, `p` = pizzas, `t` = pizza_types.

| Futuro arquivo SQL / pergunta | Fontes e colunas | Grão de saída | Fórmula | Aceite mensurável |
|---|---|---|---|---|
| 01_vendas_mensais / Como evoluem as vendas? | o.order_id/date; d.order_id/pizza_id/quantity; p.pizza_id/price | Um mês com pedidos | Soma quantity×price; pedidos distintos; unidades | Receita soma ao total e pedidos mensais somam aos pedidos globais |
| 02_ranking_pizzas / Quais variantes lideram receita? | d.pizza_id/quantity; p.pizza_id/pizza_type_id/size/price; t.pizza_type_id/name | Uma variante com venda, identificada por pizza_id | Receita por variante e rank decrescente | PK variante única; soma receita = total; empates com mesmo rank; nome e tamanho explícitos |
| 03_pedidos_dia_semana / Em quais dias há mais pedidos? | o.order_id/date | Um dia da semana observado, ISO 1–7 | COUNT de pedidos; CASE para rótulo | Soma pedidos = total; domínio ISO válido |
| 04_pedidos_hora / Quais horários concentram pedidos? | o.order_id/time | Uma hora observada 0–23 | COUNT de pedidos por hora inteira | Soma pedidos = total; hora válida |
| 05_ticket_por_pedido / Quanto vale cada pedido e qual a média? | o.order_id/date; d.order_id/pizza_id/quantity; p.pizza_id/price | Um pedido | Soma receita por pedido; média global em KPIs | Uma linha por pedido; soma receita = total; média = receita total / pedidos |
| 06_receita_categoria / Quais categorias lideram? | d.pizza_id/quantity; p.pizza_id/pizza_type_id/price; t.pizza_type_id/category | Uma categoria com venda | Soma quantity×price | Soma receita = mensal = ranking |
| 07_vendas_tamanho / Como vendem os tamanhos? | d.pizza_id/quantity; p.pizza_id/size/price | Um tamanho com venda | Receita e soma quantity | Soma receita e unidades = total |
| 08_concentracao_pizzas / Quantos tipos de pizza representam pelo menos 80% da receita? | d.pizza_id/quantity; p.pizza_id/pizza_type_id/price; t.pizza_type_id/name | Um tipo com venda em ordem de receita | Participação e receita acumulada / receita global via janela ROWS; quantidade e percentual dos tipos necessários para atingir 80% | Acumulado não decrescente; último = 100%; soma receita = total; corte inclui o tipo que atinge ou ultrapassa 80% |
| 09_quantidade_por_pedido / Quantas pizzas há por pedido? | o.order_id; d.order_id/quantity | Um pedido | SUM(quantity), não COUNT de linhas | PK pedido única; soma unidades = total |
| 10_kpis / Quanto vendeu e qual o ticket? | o.order_id/date; d.order_id/pizza_id/quantity; p.pizza_id/price | Uma linha global | Receita, pedidos, unidades; média receita por pedido e média unidades por pedido | Uma linha; reconciliação com 01/05/07/09; denominadores positivos |
| 11_ranking_tipos_pizza / Quais tipos lideram receita ao reunir os tamanhos? | d.pizza_id/quantity; p.pizza_id/pizza_type_id/price; t.pizza_type_id/name | Um tipo com venda, identificado por pizza_type_id | Soma quantity×price por tipo e rank decrescente | PK tipo única; soma receita = total; receita de cada tipo = soma de suas variantes no mart 02; empates com mesmo rank |

Os marts 02 e 11 são visões alternativas da mesma receita, em grãos distintos:
não somar seus totais entre si. Ambos leem diretamente refined. A reconciliação
agrupa as variantes do mart 02 pelo tipo e compara com o mart 11; isso é uma
verificação de qualidade, não dependência de criação entre marts. Usar a chave,
não apenas o nome, para identificar produtos.

Dias e horas sem pedidos não serão preenchidos como zero nesta proposta:
ausência de registro não comprova loja aberta sem venda. Nenhum mart permite
inferir número de clientes. Quantidade de pedidos por categoria não é aditiva
entre categorias: um pedido pode conter várias. Receita, unidades e pedidos
mensais são aditivos em partições disjuntas; tickets e percentuais não são.

### Pareto da receita — contrato do mart 08

- **Pergunta:** quantos tipos de pizza, e qual proporção dos tipos com vendas,
  são necessários para atingir pelo menos 80% da receita estimada?
- **População:** tipos com vendas no período analisado; variantes sem venda
  não ampliam o denominador. Agregar tamanhos por pizza_type_id.
- **Ordenação:** receita decrescente, com pizza_type_id crescente como desempate.
- **Saída:** uma linha por tipo com receita, posição, participação percentual,
  percentual acumulado e indicação de pertencimento ao grupo de 80%. Quantidade
  e percentual de tipos desse grupo também saem prontos do SQL, podendo ser
  repetidos nas linhas como medidas globais, que não devem ser somadas.
- **Corte:** menor posição cujo acumulado alcance 80% da receita total. Incluir
  essa posição no grupo, inclusive se ultrapassar o limite. Comparar valores
  antes de arredondar percentuais para apresentação.
- **Fórmula do resumo:** número de tipos até o corte / total de tipos com vendas
  × 100. É uma medida observada, não uma hipótese de que a relação será 80/20.
- **Erro:** receita total zero impede calcular participação e corte; falhar
  explicitamente, conforme a spec de marts.
- **Aceite:** o grupo alcança pelo menos 80% e o prefixo anterior fica abaixo
  de 80%; receita de todos os tipos reconcilia com o total. Em exemplo sintético
  com receitas 60, 25 e 15 USD, o grupo contém os dois primeiros tipos e alcança
  85%; não contém somente o primeiro nem exclui o tipo que cruza o limite.

O mart continua em `08_concentracao_pizzas.sql`; Pareto é a definição explícita
desse candidato, evitando duplicar o mesmo indicador com outro nome.

## Perguntas que a base não sustenta

Lucro e margem (sem custos); clientes únicos, retenção e recompra (sem cliente);
cancelamento (sem status); estoque e consumo físico de ingredientes (sem saldo
ou ficha técnica); eficácia causal de promoção (sem campanha/controle); tempo
de preparo/entrega (sem eventos). Um único ano permite descrever variações
mensais, não comprovar sazonalidade recorrente. Baixa receita isolada não
justifica retirar produto do cardápio. Valores USD não serão rotulados em BRL.
