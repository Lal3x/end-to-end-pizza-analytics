-- Qual a cesta? Grão final e da CTE: um pedido.
WITH itens AS (
    SELECT orderID, count(*) AS unidades_itens FROM refined.order_items GROUP BY orderID
)
SELECT o.id AS orderID, o.nItems AS unidades, i.unidades_itens
FROM refined.orders o JOIN itens i ON o.id = i.orderID;
