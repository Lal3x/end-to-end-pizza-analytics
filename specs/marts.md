# Etapa 3 — Marts Pizza Paradise

Status: contrato inicial adaptado; implementar após refined validada.

## CONTEXTO

Treze candidatos de negócio em indicadores.md, com contratos em
docs/contratos-indicadores.md. O Python executa SQL, sem fórmulas ocultas.

## STACK

Python 3.13, uv, DuckDB e SQL; sem outro banco ou orquestrador.

## O QUE JÁ EXISTE

Nova fonte inspecionada, migração de ingestão autorizada e modelo atualizado.
Ainda não há refined validada, marts ou dashboard da nova fonte.

## ARTEFATOS A PRODUZIR

sql/marts/01 a 13 e pipeline/marts.py; comando futuro
uv run python -m pipeline.marts.

## SPEC

1. Ler somente as cinco tabelas refined. Um SELECT por arquivo NN_nome.sql,
   pergunta/grão no comentário inicial, grão de cada CTE declarado.
   Motivo: fonte e fórmulas rastreáveis.
2. Executar em ordem de prefixo; tabela = nome sem NN_ e extensão.
   CTAS com o SQL original, removendo só espaços e ponto e vírgula final.
   Nenhuma fórmula em Python. Motivo: uma pergunta, um arquivo, uma tabela.
3. Recriar marts numa transação única, incluindo DROP do schema. Arquivo
   removido não deixa tabela antiga. Motivo: nenhuma camada parcialmente nova.
4. Antes da escrita, validar fontes, prefixos, nomes duplicados e pasta não
   vazia. SQL inválido, mart obrigatório vazio ou qualidade divergente: saída 1,
   diagnóstico e rollback integral; fechar conexão.
5. order_items preserva repetições. JOIN com products/orders é N:1 e deve
   preservar quantidade de ocorrências. orders.total/nItems são medidas de
   pedido e não podem ser somadas depois de JOIN 1:N sem reagrupamento.
   Motivo: evitar perda de unidades ou multiplicação de receita.
6. Reconciliações: receita por mês/SKU/Name/categoria/tamanho/loja = total de
   pedidos; unidades por tamanho = nItems; contagens de pedidos por mês/semana/
   hora incluindo grupo sem hora/loja = total. Clientes distintos não são
   aditivos entre lojas ou meses. Ticket não é soma nem média de médias.
7. Pareto consolidado por Name; incluir posição que atinge 80%, sem arredondar
   antes do corte. Receita zero falha. Data sem hora não vira hora zero.
8. Logs UTF-8 com contagem do banco e total apenas após COMMIT.
   Motivo: anunciar somente versão publicada.

## CRITÉRIOS DE ACEITE

Treze saídas não vazias com grãos únicos conforme contrato; reconciliações
financeiras exatas após regra monetária validada. JOIN não perde nem duplica
ocorrências além da fonte. Um pedido com dois itens conta uma vez no ticket.
Duas linhas idênticas de item contam duas unidades. Datas sem hora entram no
grupo próprio. SQL com erro, vazio ou prefixo inválido preserva versão anterior.
Remover arquivo remove mart; repetir execução mantém resultado.

## ENTREGA

Specs antes do código; SQLs revisados; executor com docstring; testes sintéticos
DuckDB temporário real, sem rede/dados do projeto; resultados, cobertura e
limitações medidas. Pendências de moeda e tempo precisam ser resolvidas antes
dos SQLs finais.
