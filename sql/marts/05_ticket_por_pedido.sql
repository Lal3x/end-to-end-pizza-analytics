-- Quanto vale cada venda? Grão final e da CTE: um pedido.
WITH itens AS (
    SELECT i.orderID, sum(p.Price) AS receita_itens
    FROM refined.order_items i JOIN refined.products p ON p.SKU = i.SKU
    GROUP BY i.orderID
)
SELECT o.id AS orderID, o.total AS receita, i.receita_itens
FROM refined.orders o JOIN itens i ON i.orderID = o.id;
