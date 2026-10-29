-- Quais horas concentram pedidos? Grão: hora em São Paulo ou grupo sem hora (NULL).
-- Referência comum de visualização; não representa o fuso comercial das lojas.
SELECT hour(timezone('America/Sao_Paulo', order_timestamp)) AS hora_local,
       'America/Sao_Paulo' AS fuso_horario,
       order_timestamp IS NULL AS hora_nao_informada, count(*) AS pedidos
FROM refined.orders GROUP BY 1, 2, 3 ORDER BY hora_local NULLS LAST;
