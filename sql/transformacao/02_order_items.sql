-- Grão: uma ocorrência de SKU no pedido, sem PK natural de linha.
-- Não aplicar DISTINCT: linhas iguais representam unidades legítimas.
SELECT
    SKU,
    CAST(orderID AS VARCHAR) AS orderID
FROM raw.order_items;
