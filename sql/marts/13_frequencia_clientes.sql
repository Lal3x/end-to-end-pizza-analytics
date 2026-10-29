-- Quantos clientes repetem? Grão final: frequência de pedidos por cliente.
-- CTE frequencias: um cliente com compra; distribuicao: uma frequência observada.
WITH frequencias AS (
    SELECT c.id AS customerId, count(*) AS frequencia
    FROM refined.orders o JOIN refined.customers c ON c.id = o.customerId
    GROUP BY c.id
), distribuicao AS (
    SELECT frequencia, count(*) AS clientes FROM frequencias GROUP BY frequencia
)
SELECT *, clientes * 1.0 / sum(clientes) OVER () AS participacao_clientes,
       coalesce(sum(clientes) FILTER (WHERE frequencia > 1) OVER (), 0) * 1.0
           / sum(clientes) OVER () AS proporcao_recompra
FROM distribuicao ORDER BY frequencia;
