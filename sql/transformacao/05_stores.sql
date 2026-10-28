-- Grão: uma loja (id), após validar conflito de chave e conversões.
-- Zipcode permanece texto. Distance é medida sem unidade comprovada.
WITH fonte AS (
    SELECT DISTINCT * FROM raw.stores
)
SELECT
    id,
    zipcode,
    state_abbr,
    CAST(latitude AS DOUBLE) AS latitude,
    CAST(longitude AS DOUBLE) AS longitude,
    city,
    state,
    CAST(distance AS DOUBLE) AS distance
FROM fonte;
