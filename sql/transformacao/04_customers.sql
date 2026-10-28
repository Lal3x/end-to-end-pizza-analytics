-- Grão: um cliente (id), após validar conflito de chave e coordenadas.
WITH fonte AS (
    SELECT DISTINCT * FROM raw.customers
)
SELECT
    id,
    CAST(latitude AS DOUBLE) AS latitude,
    CAST(longitude AS DOUBLE) AS longitude
FROM fonte;
