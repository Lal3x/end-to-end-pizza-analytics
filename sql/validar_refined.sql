-- Auditoria de entrada: cada linha retornada impede publicar marts.
WITH itens AS ( -- um pedido
    SELECT i.orderID, count(*) AS unidades, sum(p.Price) AS receita
    FROM refined.order_items i LEFT JOIN refined.products p USING (SKU) GROUP BY i.orderID
)
SELECT 'orders: chave inválida' AS erro WHERE EXISTS (
    SELECT id FROM refined.orders GROUP BY id HAVING id IS NULL OR trim(id)='' OR count(*)<>1
)
UNION ALL SELECT 'products: chave inválida' WHERE EXISTS (
    SELECT SKU FROM refined.products GROUP BY SKU HAVING SKU IS NULL OR trim(SKU)='' OR count(*)<>1
)
UNION ALL SELECT 'customers: chave inválida' WHERE EXISTS (
    SELECT id FROM refined.customers GROUP BY id HAVING id IS NULL OR trim(id)='' OR count(*)<>1
)
UNION ALL SELECT 'stores: chave inválida' WHERE EXISTS (
    SELECT id FROM refined.stores GROUP BY id HAVING id IS NULL OR trim(id)='' OR count(*)<>1
)
UNION ALL SELECT 'orders: cliente órfão' WHERE EXISTS (
    SELECT 1 FROM refined.orders o ANTI JOIN refined.customers c ON c.id=o.customerId
)
UNION ALL SELECT 'orders: loja órfã' WHERE EXISTS (
    SELECT 1 FROM refined.orders o ANTI JOIN refined.stores s ON s.id=o.storeId
)
UNION ALL SELECT 'order_items: pedido órfão' WHERE EXISTS (
    SELECT 1 FROM refined.order_items i ANTI JOIN refined.orders o ON o.id=i.orderID
)
UNION ALL SELECT 'order_items: SKU órfão' WHERE EXISTS (
    SELECT 1 FROM refined.order_items i ANTI JOIN refined.products p USING (SKU)
)
UNION ALL SELECT 'products: nome/categoria/tamanho/preço inválidos' WHERE EXISTS (
    SELECT 1 FROM refined.products WHERE Name IS NULL OR trim(Name)='' OR Category IS NULL
        OR trim(Category)='' OR Size IS NULL OR trim(Size)='' OR Price IS NULL OR Price<0
)
UNION ALL SELECT 'products: Name/Category conflitante' WHERE EXISTS (
    SELECT Name FROM refined.products GROUP BY Name HAVING count(DISTINCT Category)<>1
)
UNION ALL SELECT 'stores: localização ausente' WHERE EXISTS (
    SELECT 1 FROM refined.stores WHERE city IS NULL OR trim(city)='' OR state IS NULL OR trim(state)=''
)
UNION ALL SELECT 'orders: medidas/data/precisão inválidas' WHERE EXISTS (
    SELECT 1 FROM refined.orders WHERE total IS NULL OR total<0 OR nItems IS NULL OR nItems<=0
       OR order_date IS NULL OR timestamp_precision IS NULL
       OR timestamp_precision NOT IN ('date','minute','second')
       OR (timestamp_precision='date') <> (order_timestamp IS NULL)
       OR (order_timestamp IS NOT NULL AND timezone('UTC',order_timestamp)::DATE<>order_date)
)
UNION ALL SELECT 'orders: quantidade/receita não reconciliam' WHERE EXISTS (
    SELECT 1 FROM refined.orders o LEFT JOIN itens i ON o.id=i.orderID
    WHERE i.unidades IS DISTINCT FROM o.nItems OR i.receita IS DISTINCT FROM o.total
)
UNION ALL SELECT 'Pareto: receita total não positiva' WHERE
    coalesce((SELECT sum(total) FROM refined.orders),0)<=0;
