-- Quando há mais pedidos? Grão: um dia ISO observado (segunda=1, domingo=7).
SELECT isodow(order_date) AS dia_iso, count(*) AS pedidos
FROM refined.orders GROUP BY 1 ORDER BY dia_iso;
