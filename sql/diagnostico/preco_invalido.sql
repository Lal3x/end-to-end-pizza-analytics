-- Diagnóstico: preço textual com até duas casas, sem arredondamento tolerado.
SELECT count(*)
FROM raw.products
WHERE NOT regexp_full_match(Price, '[0-9]+([.][0-9]{1,2})?')
   OR try_cast(Price AS DECIMAL(18,2)) IS NULL;
