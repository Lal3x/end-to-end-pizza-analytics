-- Grão: um SKU, após validar conflitos da PK e formato monetário na RAW.
-- Launch aceita somente ISO exato ou ISO com uma vírgula terminal.
WITH fonte AS (
    SELECT DISTINCT * FROM raw.products
), lancamento AS (
    SELECT *,
        CASE
            WHEN regexp_full_match(Launch, '[0-9]{4}-[0-9]{2}-[0-9]{2}')
                THEN Launch
            WHEN regexp_full_match(Launch, '[0-9]{4}-[0-9]{2}-[0-9]{2},')
                THEN left(Launch, 10)
            ELSE error('Launch com formato desconhecido')
        END AS launch_normalizado
    FROM fonte
)
SELECT
    SKU,
    Name,
    CAST(Price AS DECIMAL(18,2)) AS Price,
    Category,
    Size,
    Ingredients,
    CAST(strptime(launch_normalizado, '%Y-%m-%d') AS DATE) AS Launch
FROM lancamento;
