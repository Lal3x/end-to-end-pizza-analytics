-- Como evoluem as vendas? Grão: um ano/mês observado, representado pelo primeiro dia.
SELECT date_trunc('month', order_date)::DATE AS mes,
       count(*) AS pedidos, sum(nItems) AS unidades, sum(total) AS receita
FROM refined.orders
GROUP BY 1
ORDER BY mes;
