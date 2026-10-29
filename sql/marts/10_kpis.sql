-- Quais totais e médias? Grão: uma linha global da janela observada.
SELECT count(*) AS pedidos, sum(nItems) AS unidades, sum(total) AS receita,
       sum(total) / count(*) AS ticket_medio,
       sum(nItems) * 1.0 / count(*) AS unidades_por_pedido,
       min(order_date) AS data_inicial, max(order_date) AS data_final
FROM refined.orders;
