# Modelo relacional — Pizza Paradise

Fonte ativa: Pizza Paradise, notebook Observable versão 398, dados fictícios.
A migração foi autorizada após a avaliação em docs/avaliacao-pizza-paradise.md.
O modelo Maven anterior permanece nos commits e registros históricos.

| Tabela | Colunas | Grão / chave |
|---|---|---|
| orders | id, customerId, storeId, orderDate, nItems, total | Um pedido, PK id |
| order_items | SKU, orderID | Uma ocorrência de produto no pedido; sem PK natural de linha |
| products | SKU, Name, Price, Category, Size, Ingredients, Launch | Um SKU (variante), PK SKU |
| customers | id, latitude, longitude | Um cliente fictício, PK id |
| stores | id, zipcode, state_abbr, latitude, longitude, city, state, distance | Uma loja, PK id |

Relações N:1: orders.customerId → customers.id; orders.storeId → stores.id;
order_items.orderID → orders.id; order_items.SKU → products.SKU.
Todos os pais são únicos e as quatro FKs têm zero órfãos na versão inspecionada.

## Evidência e granularidade

2.046.713 pedidos, 2.916.015 ocorrências de itens, 34.761 clientes, 32 lojas,
36 SKUs (9 nomes e 4 tamanhos), período 2020–2022.
Zero nulos nas colunas inspecionadas. Evidência:
[evidencias/pizza-paradise-inspecao.json](evidencias/pizza-paradise-inspecao.json).

54.041 repetições exatas além da primeira em order_items são ocorrências
necessárias: COUNT por pedido = nItems, soma do catálogo em centavos = total.
Não deduplicar esta tabela. Na refined ela não ganhará uma PK natural inventada.
Uma agregação por orderID/SKU teria outro grão e deve ser explicitamente definida.

Pedidos guardam total e nItems no grão de pedido; após JOIN com itens, não somar
esses campos repetidos. Receita dos itens usa cada ocorrência × preço de SKU.
SKU identifica variante; Name consolida tamanhos, mas não é ID independente.
Validar que cada Name aponta para uma categoria consistente antes do ranking
consolidado; não inventar pizza_type_id na origem.

## Representação das fontes e tipos

Três CSVs UTF-8 e dois Parquets. RAW mantém CSV como VARCHAR e Parquet nos
tipos nativos: orders.id/nItems INTEGER, total DOUBLE, outros VARCHAR;
order_items.orderID INTEGER e SKU VARCHAR. Isso preserva a representação
tipada da fonte, ao contrário do contrato anterior de quatro CSVs.
Na refined, IDs são VARCHAR e dinheiro DECIMAL(18,2).

orderDate mistura segundos+Z, minutos+Z e data sem horário (116 pedidos).
Não interpretar esses 116 como pedidos à meia-noite sem evidência.
Na refined, order_date é DATE; order_timestamp mantém UTC e fica nulo quando
somente a data é conhecida. timestamp_precision distingue second, minute e date.
Launch contém vírgula terminal em PZ026/PZ027 na RAW; a correção aprovada remove
essa vírgula somente nesses valores e publica DATE na refined.
Contrato: specs/transformacao.md.
Coordenadas não demonstram rota ou duração. distance não tem unidade comprovada.
Não há custos, pagamento, status de cancelamento ou eventos de entrega.
