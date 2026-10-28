-- Grão: um pedido (id), após validar conflitos na PK da RAW.
-- Preserva orderDate e indica sua precisão; data sem hora não vira meia-noite.
-- Pré-condições: nulos/domínios validados e desvio monetário <= 1e-9.
WITH fonte AS (
    SELECT DISTINCT * FROM raw.orders
), temporal AS (
    SELECT *,
        CASE
            WHEN regexp_full_match(orderDate, '[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z')
                THEN 'second'
            WHEN regexp_full_match(orderDate, '[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}Z')
                THEN 'minute'
            WHEN regexp_full_match(orderDate, '[0-9]{4}-[0-9]{2}-[0-9]{2}')
                THEN 'date'
            ELSE error('orderDate com formato desconhecido')
        END AS timestamp_precision
    FROM fonte
)
SELECT
    CAST(id AS VARCHAR) AS id,
    customerId,
    storeId,
    orderDate,
    nItems,
    CAST(total AS DECIMAL(18,2)) AS total,
    CAST(strptime(left(orderDate, 10), '%Y-%m-%d') AS DATE) AS order_date,
    CASE timestamp_precision
        WHEN 'second' THEN strptime(orderDate, '%Y-%m-%dT%H:%M:%SZ') AT TIME ZONE 'UTC'
        WHEN 'minute' THEN strptime(orderDate, '%Y-%m-%dT%H:%MZ') AT TIME ZONE 'UTC'
        ELSE NULL::TIMESTAMPTZ
    END AS order_timestamp,
    timestamp_precision
FROM temporal;
