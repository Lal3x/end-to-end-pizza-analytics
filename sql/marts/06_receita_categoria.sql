-- Quais categorias lideram? Grão: uma categoria com venda.
SELECT p.Category, count(*) AS unidades, sum(p.Price) AS receita
FROM refined.order_items i JOIN refined.products p ON p.SKU = i.SKU
JOIN refined.orders o ON o.id = i.orderID
GROUP BY p.Category ORDER BY receita DESC, p.Category;
