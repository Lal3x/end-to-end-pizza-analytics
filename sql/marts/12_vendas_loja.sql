-- Como cada loja vende? Grão: uma loja com venda, sem multiplicar pedidos por itens.
SELECT s.id AS storeId, s.city, s.state, count(*) AS pedidos,
       sum(o.nItems) AS unidades, sum(o.total) AS receita,
       sum(o.total) / count(*) AS ticket_medio
FROM refined.orders o JOIN refined.stores s ON s.id = o.storeId
GROUP BY s.id, s.city, s.state ORDER BY receita DESC, storeId;
