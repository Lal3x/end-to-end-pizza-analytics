-- Auditoria independente: linhas retornadas são violações, não dados publicados.
WITH totais AS ( -- uma linha global
    SELECT count(*) AS pedidos, sum(nItems) AS unidades, sum(total) AS receita,
           min(order_date) AS inicio, max(order_date) AS fim FROM refined.orders
), medidas_itens AS ( -- uma dimensão de item e sua chave
    SELECT 'SKU' AS dimensao, p.SKU AS chave, count(*) AS unidades, sum(p.Price) AS receita
    FROM refined.order_items i JOIN refined.products p USING (SKU) GROUP BY p.SKU
    UNION ALL
    SELECT 'Name', p.Name, count(*), sum(p.Price)
    FROM refined.order_items i JOIN refined.products p USING (SKU) GROUP BY p.Name
    UNION ALL
    SELECT 'Category', p.Category, count(*), sum(p.Price)
    FROM refined.order_items i JOIN refined.products p USING (SKU) GROUP BY p.Category
    UNION ALL
    SELECT 'Size', p.Size, count(*), sum(p.Price)
    FROM refined.order_items i JOIN refined.products p USING (SKU) GROUP BY p.Size
), medidas_publicadas AS ( -- mesma dimensão/chave, em quatro marts
    SELECT 'SKU' AS dimensao, SKU AS chave, unidades, receita FROM marts.ranking_pizzas
    UNION ALL SELECT 'Name', Name, unidades, receita FROM marts.ranking_tipos_pizza
    UNION ALL SELECT 'Category', Category, unidades, receita FROM marts.receita_categoria
    UNION ALL SELECT 'Size', Size, unidades, receita FROM marts.vendas_tamanho
), diferencas_itens AS ( -- diferenças de valor e multiplicidade, nos dois sentidos
    (SELECT * FROM medidas_itens EXCEPT ALL SELECT * FROM medidas_publicadas)
    UNION ALL (SELECT * FROM medidas_publicadas EXCEPT ALL SELECT * FROM medidas_itens)
), pedidos_esperados AS ( -- uma partição de pedidos e sua chave
    SELECT 'mes' AS dimensao, date_trunc('month',order_date)::DATE::VARCHAR AS chave,
           count(*) AS pedidos FROM refined.orders GROUP BY 2
    UNION ALL SELECT 'dia', isodow(order_date)::VARCHAR, count(*) FROM refined.orders GROUP BY 2
    UNION ALL SELECT 'hora', coalesce(hour(timezone('America/Sao_Paulo',order_timestamp))::VARCHAR,'sem hora'), count(*)
    FROM refined.orders GROUP BY 2
    UNION ALL SELECT 'loja', storeId, count(*) FROM refined.orders GROUP BY storeId
), pedidos_publicados AS ( -- mesma partição/chave
    SELECT 'mes' AS dimensao, mes::VARCHAR AS chave, pedidos FROM marts.vendas_mensais
    UNION ALL SELECT 'dia', dia_iso::VARCHAR, pedidos FROM marts.pedidos_dia_semana
    UNION ALL SELECT 'hora', coalesce(hora_local::VARCHAR,'sem hora'), pedidos FROM marts.pedidos_hora
    UNION ALL SELECT 'loja', storeId, pedidos FROM marts.vendas_loja
), diferencas_pedidos AS (
    (SELECT * FROM pedidos_esperados EXCEPT ALL SELECT * FROM pedidos_publicados)
    UNION ALL (SELECT * FROM pedidos_publicados EXCEPT ALL SELECT * FROM pedidos_esperados)
), cestas AS ( -- um pedido observado nos itens
    SELECT i.orderID, count(*) AS unidades, sum(p.Price) AS receita
    FROM refined.order_items i JOIN refined.products p USING (SKU) GROUP BY i.orderID
), frequencias AS ( -- um cliente com compras
    SELECT customerId, count(*) AS frequencia FROM refined.orders GROUP BY customerId
), distribuicao AS ( -- uma frequência esperada
    SELECT frequencia, count(*) AS clientes FROM frequencias GROUP BY frequencia
), ranking_sku AS ( -- um SKU, posição independente sobre receita publicada
    SELECT SKU, dense_rank() OVER (ORDER BY receita DESC) AS posicao FROM marts.ranking_pizzas
), ranking_nome AS ( -- um nome, posição independente sobre receita publicada
    SELECT Name, dense_rank() OVER (ORDER BY receita DESC) AS posicao FROM marts.ranking_tipos_pizza
), pareto AS ( -- um nome, acumulado calculado por correlação em vez de janela
    SELECT p.*, (SELECT sum(q.receita) FROM marts.ranking_tipos_pizza q
        WHERE q.receita>p.receita OR (q.receita=p.receita AND q.Name<=p.Name)) AS acumulado,
        (SELECT count(*) FROM marts.ranking_tipos_pizza q
        WHERE q.receita>p.receita OR (q.receita=p.receita AND q.Name<=p.Name)) AS ordem_esperada
    FROM marts.concentracao_pizzas p
), graos AS ( -- uma violação de grão
    SELECT 'vendas_mensais' AS tabela FROM marts.vendas_mensais GROUP BY mes HAVING mes IS NULL OR count(*)<>1
    UNION ALL SELECT 'ranking_pizzas' FROM marts.ranking_pizzas GROUP BY SKU HAVING SKU IS NULL OR count(*)<>1
    UNION ALL SELECT 'pedidos_dia_semana' FROM marts.pedidos_dia_semana GROUP BY dia_iso HAVING dia_iso IS NULL OR count(*)<>1
    UNION ALL SELECT 'pedidos_hora' FROM marts.pedidos_hora GROUP BY hora_local HAVING count(*)<>1
    UNION ALL SELECT 'ticket_por_pedido' FROM marts.ticket_por_pedido GROUP BY orderID HAVING orderID IS NULL OR count(*)<>1
    UNION ALL SELECT 'receita_categoria' FROM marts.receita_categoria GROUP BY Category HAVING Category IS NULL OR count(*)<>1
    UNION ALL SELECT 'vendas_tamanho' FROM marts.vendas_tamanho GROUP BY Size HAVING Size IS NULL OR count(*)<>1
    UNION ALL SELECT 'concentracao_pizzas' FROM marts.concentracao_pizzas GROUP BY Name HAVING Name IS NULL OR count(*)<>1
    UNION ALL SELECT 'quantidade_por_pedido' FROM marts.quantidade_por_pedido GROUP BY orderID HAVING orderID IS NULL OR count(*)<>1
    UNION ALL SELECT 'ranking_tipos_pizza' FROM marts.ranking_tipos_pizza GROUP BY Name HAVING Name IS NULL OR count(*)<>1
    UNION ALL SELECT 'vendas_loja' FROM marts.vendas_loja GROUP BY storeId HAVING storeId IS NULL OR count(*)<>1
    UNION ALL SELECT 'frequencia_clientes' FROM marts.frequencia_clientes GROUP BY frequencia HAVING frequencia IS NULL OR count(*)<>1
)
SELECT 'Grão inválido: ' || tabela AS erro FROM graos
UNION ALL SELECT 'Receita/unidades por dimensão de item' WHERE EXISTS (SELECT 1 FROM diferencas_itens)
UNION ALL SELECT 'Contagens por mês/dia/hora/loja' WHERE EXISTS (SELECT 1 FROM diferencas_pedidos)
UNION ALL SELECT 'Mês: receita/unidades' WHERE EXISTS (
    SELECT 1 FROM marts.vendas_mensais m WHERE m.receita IS DISTINCT FROM
        (SELECT sum(total) FROM refined.orders WHERE date_trunc('month',order_date)::DATE=m.mes)
        OR m.unidades IS DISTINCT FROM
        (SELECT sum(nItems) FROM refined.orders WHERE date_trunc('month',order_date)::DATE=m.mes)
)
UNION ALL SELECT 'Loja: receita/unidades/ticket/localização' WHERE EXISTS (
    SELECT 1 FROM marts.vendas_loja m JOIN refined.stores s ON s.id=m.storeId
    WHERE m.city IS DISTINCT FROM s.city OR m.state IS DISTINCT FROM s.state
        OR m.receita IS DISTINCT FROM (SELECT sum(total) FROM refined.orders WHERE storeId=m.storeId)
        OR m.unidades IS DISTINCT FROM (SELECT sum(nItems) FROM refined.orders WHERE storeId=m.storeId)
        OR m.ticket_medio IS NULL OR NOT isfinite(m.ticket_medio)
        OR abs(m.ticket_medio-m.receita/m.pedidos)>1e-9
)
UNION ALL SELECT 'Hora não informada' WHERE EXISTS (
    SELECT 1 FROM marts.pedidos_hora WHERE hora_nao_informada IS DISTINCT FROM (hora_local IS NULL)
        OR fuso_horario IS DISTINCT FROM 'America/Sao_Paulo'
)
UNION ALL SELECT 'Ticket por pedido' WHERE EXISTS (
    SELECT 1 FROM refined.orders o FULL JOIN marts.ticket_por_pedido m ON m.orderID=o.id
    LEFT JOIN cestas c ON c.orderID=o.id WHERE o.id IS NULL OR m.orderID IS NULL
        OR m.receita IS DISTINCT FROM o.total OR m.receita_itens IS DISTINCT FROM c.receita
)
UNION ALL SELECT 'Quantidade por pedido' WHERE EXISTS (
    SELECT 1 FROM refined.orders o FULL JOIN marts.quantidade_por_pedido m ON m.orderID=o.id
    LEFT JOIN cestas c ON c.orderID=o.id WHERE o.id IS NULL OR m.orderID IS NULL
        OR m.unidades IS DISTINCT FROM o.nItems OR m.unidades_itens IS DISTINCT FROM c.unidades
)
UNION ALL SELECT 'KPIs: grão/totais/médias/período' WHERE
    (SELECT count(*) FROM marts.kpis)<>1 OR EXISTS (
        SELECT 1 FROM marts.kpis k CROSS JOIN totais t WHERE k.pedidos IS DISTINCT FROM t.pedidos
        OR k.unidades IS DISTINCT FROM t.unidades OR k.receita IS DISTINCT FROM t.receita
        OR k.data_inicial IS DISTINCT FROM t.inicio OR k.data_final IS DISTINCT FROM t.fim
        OR k.ticket_medio IS NULL OR NOT isfinite(k.ticket_medio)
        OR k.unidades_por_pedido IS NULL OR NOT isfinite(k.unidades_por_pedido)
        OR abs(k.ticket_medio-t.receita/t.pedidos)>1e-9
        OR abs(k.unidades_por_pedido-t.unidades*1.0/t.pedidos)>1e-9
    )
UNION ALL SELECT 'Ranking: posição ou descrição' WHERE EXISTS (
    SELECT 1 FROM marts.ranking_pizzas m JOIN ranking_sku r USING (SKU)
    JOIN refined.products p USING (SKU) WHERE m.posicao IS DISTINCT FROM r.posicao
        OR m.Name IS DISTINCT FROM p.Name OR m.Size IS DISTINCT FROM p.Size
) OR EXISTS (
    SELECT 1 FROM marts.ranking_tipos_pizza m JOIN ranking_nome r USING (Name)
    WHERE m.posicao IS DISTINCT FROM r.posicao
)
UNION ALL SELECT 'Pareto: receita por nome' WHERE EXISTS (
    (SELECT Name, receita FROM marts.concentracao_pizzas EXCEPT ALL SELECT Name, receita FROM marts.ranking_tipos_pizza)
    UNION ALL (SELECT Name, receita FROM marts.ranking_tipos_pizza EXCEPT ALL SELECT Name, receita FROM marts.concentracao_pizzas)
)
UNION ALL SELECT 'Pareto: ordem/acumulado/corte/percentuais' WHERE EXISTS (
    SELECT 1 FROM pareto p CROSS JOIN totais t
    WHERE p.ordem IS DISTINCT FROM p.ordem_esperada OR p.receita_total IS DISTINCT FROM t.receita
        OR p.receita_acumulada IS DISTINCT FROM p.acumulado
        OR p.grupo_80 IS DISTINCT FROM ((p.acumulado-p.receita)*100<t.receita*80)
        OR p.participacao IS NULL OR NOT isfinite(p.participacao)
        OR p.participacao_acumulada IS NULL OR NOT isfinite(p.participacao_acumulada)
        OR abs(p.participacao-p.receita/t.receita)>1e-9
        OR abs(p.participacao_acumulada-p.acumulado/t.receita)>1e-9
        OR p.produtos_80 IS DISTINCT FROM (SELECT count(*) FROM pareto WHERE (acumulado-receita)*100<receita_total*80)
        OR p.proporcao_produtos_80 IS NULL OR NOT isfinite(p.proporcao_produtos_80)
        OR abs(p.proporcao_produtos_80-p.produtos_80*1.0/(SELECT count(*) FROM pareto))>1e-9
)
UNION ALL SELECT 'Clientes: distribuição' WHERE EXISTS (
    (SELECT frequencia, clientes FROM distribuicao EXCEPT ALL SELECT frequencia, clientes FROM marts.frequencia_clientes)
    UNION ALL (SELECT frequencia, clientes FROM marts.frequencia_clientes EXCEPT ALL SELECT frequencia, clientes FROM distribuicao)
)
UNION ALL SELECT 'Clientes: participações/recompra' WHERE EXISTS (
    SELECT 1 FROM marts.frequencia_clientes m
    WHERE m.participacao_clientes IS NULL OR NOT isfinite(m.participacao_clientes)
        OR m.proporcao_recompra IS NULL OR NOT isfinite(m.proporcao_recompra)
        OR abs(m.participacao_clientes-m.clientes*1.0/(SELECT count(*) FROM frequencias))>1e-9
        OR abs(m.proporcao_recompra-(SELECT count(*) FROM frequencias WHERE frequencia>1)*1.0/(SELECT count(*) FROM frequencias))>1e-9
);
