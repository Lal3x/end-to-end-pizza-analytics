-- Quantos produtos fazem 80%? Grão final e das CTEs: um Name com venda.
WITH vendas AS (
    SELECT p.Name, sum(p.Price) AS receita
    FROM refined.order_items i JOIN refined.products p ON p.SKU = i.SKU
    JOIN refined.orders o ON o.id = i.orderID
    GROUP BY p.Name
), acumulados AS (
    SELECT *, row_number() OVER (ORDER BY receita DESC, Name) AS ordem,
           sum(receita) OVER () AS receita_total,
           sum(receita) OVER (ORDER BY receita DESC, Name
               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS receita_acumulada
    FROM vendas
), grupo AS (
    SELECT *, receita / nullif(receita_total, 0) AS participacao,
           receita_acumulada / nullif(receita_total, 0) AS participacao_acumulada,
           (receita_acumulada - receita) * 100 < receita_total * 80 AS grupo_80
    FROM acumulados
)
SELECT *, count(*) FILTER (WHERE grupo_80) OVER () AS produtos_80,
       count(*) FILTER (WHERE grupo_80) OVER () * 1.0 / count(*) OVER () AS proporcao_produtos_80
FROM grupo ORDER BY ordem;
