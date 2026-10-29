-- Quais variantes lideram? Grão final e da CTE: um SKU com venda.
WITH vendas AS (
    SELECT p.SKU, p.Name, p.Size, count(*) AS unidades, sum(p.Price) AS receita
    FROM refined.order_items i
    JOIN refined.products p ON p.SKU = i.SKU
    JOIN refined.orders o ON o.id = i.orderID
    GROUP BY p.SKU, p.Name, p.Size
)
SELECT *, dense_rank() OVER (ORDER BY receita DESC) AS posicao
FROM vendas ORDER BY receita DESC, SKU;
