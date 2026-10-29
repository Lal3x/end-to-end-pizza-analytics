-- Como vendem os tamanhos? Grão: um tamanho com venda.
SELECT p.Size, count(*) AS unidades, sum(p.Price) AS receita
FROM refined.order_items i JOIN refined.products p ON p.SKU = i.SKU
JOIN refined.orders o ON o.id = i.orderID
GROUP BY p.Size ORDER BY receita DESC, p.Size;
