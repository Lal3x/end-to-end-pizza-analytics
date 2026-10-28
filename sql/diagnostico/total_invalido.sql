-- Diagnóstico: tolerância absoluta de 1e-9 somente para representação DOUBLE.
-- Qualquer linha contada impede publicar a transformação.
SELECT count(*)
FROM raw.orders
WHERE NOT isfinite(total)
   OR total < 0
   OR try_cast(total AS DECIMAL(18,2)) IS NULL
   OR abs(total - CAST(try_cast(total AS DECIMAL(18,2)) AS DOUBLE)) > 1e-9;
