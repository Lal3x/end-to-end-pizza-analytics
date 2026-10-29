# Etapa 3 — Marts Pizza Paradise

Status: implementado e executado em 28/10/2026, após revisão dos 13 indicadores.
Resultados em docs/execucao-marts.md; contratos em docs/contratos-indicadores.md.

## CONTEXTO

Treze candidatos de negócio em indicadores.md, com contratos em
docs/contratos-indicadores.md. O Python executa SQL, sem fórmulas ocultas.

## STACK

Python 3.13, uv, DuckDB e SQL; sem outro banco ou orquestrador.

## O QUE JÁ EXISTE

Cinco tabelas refined publicadas e auditadas; IDs VARCHAR, dinheiro
DECIMAL(18,2), quatro FKs válidas e reconciliação exata por pedido.
61 testes aprovados na etapa anterior. Registro: docs/execucao-transformacao.md.
Consulta somente leitura nesta revisão confirmou zero conflitos Name/Category
e 116 pedidos sem horário, todos com order_timestamp NULL. Na conclusão desta
etapa: 13 marts publicados, 86 testes e cobertura total 92,42%.

## ARTEFATOS A PRODUZIR

sql/marts/01 a 13 e pipeline/marts.py; comando
uv run python -m pipeline.marts.
Integração: executar(banco=None, pasta=None, *, con=None) aceita uma conexão
externa com transação ativa, sem iniciar/confirmar/reverter/fechar a transação.
Sem con, mantém a execução isolada; banco/con juntos são inválidos.
Contrato de composição: specs/execucao-pipeline.md.
Auditorias em sql/validar_refined.sql e sql/validar_marts.sql retornam somente
nomes de violações. O executor interrompe se qualquer consulta retornar linhas;
as fórmulas de negócio e de validação ficam no SQL, não em Python.

## SPEC

### 1. ESCOPO

Ler somente as cinco tabelas refined e escrever somente em marts. Recriar
o schema em transação única, incluindo DROP. Tabelas antigas extras desaparecem
na publicação; nunca alterar raw/refined. Motivo: evitar versão parcialmente nova.

### 2. UM ARQUIVO, UMA TABELA

Um SELECT por NN_nome.sql, com pergunta/grão inicial e grão de cada CTE.
Executar em ordem de prefixo; tabela = nome sem NN_ e extensão. CTAS com o SQL
original, removendo só espaços e ponto e vírgula final. Nenhuma fórmula em
Python. Exigir os 13 contratos aprovados; arquivo obrigatório ausente impede
a carga. Motivo: uma pergunta, um arquivo e uma tabela rastreável.

### 3. SAÍDA NA TELA

JSON UTF-8 com contagem de cada tabela lida do banco e tempo medido, somente
após COMMIT. É adaptação do log textual da referência, não o mesmo formato de
terminal. Motivo: manter relatório auditável sem anunciar publicação incompleta.

### 4. ERRO

Validar fontes, prefixos, nomes, inventário não vazio e qualidade antes do DROP.
SQL inválido, mart obrigatório vazio ou reconciliação divergente: saída 1,
diagnóstico com causa, rollback integral e conexão fechada. Motivo: o dashboard
não pode ler uma camada pela metade nem excluir silenciosamente um indicador.

#### 4.1. GRANULARIDADE E RECONCILIAÇÃO

order_items preserva repetições. JOIN com products/orders é N:1 e preserva
ocorrências; total/nItems não podem ser somados após JOIN 1:N sem reagrupamento.
Receita por mês/SKU/Name/categoria/tamanho/loja = total dos pedidos. Unidades por
tamanho = nItems; contagens por mês/semana/hora/loja = pedidos. Clientes distintos
não são aditivos entre partições; ticket não é soma nem média de médias.
Pareto por Name inclui o produto que atinge/cruza 80%, sem arredondar no corte.
Receita zero falha; data sem hora nunca vira hora zero.

### POPULAÇÃO, TEMPO E MOEDA

Todos os pedidos da refined, sem filtros silenciosos ou status inexistente.
Usar order_date para mês/dia ISO. Para hora, extrair de
timezone('America/Sao_Paulo', order_timestamp), explicitamente em SQL.
Manter sessão UTC e timestamp original da refined; publicar hora_local e
fuso_horario='America/Sao_Paulo'. Revisão autorizada em 29/10/2026 somente para
horários, sem deslocar meses/dias da fonte para outro calendário.
Não analisar a string orderDate novamente. timestamp_precision='date' exige
timestamp NULL e grupo de hora não informada; demais precisões exigem timestamp.
Datas/UTC da refined permanecem preservados. São Paulo é referência comum de
visualização, não o fuso comercial das lojas americanas.
Cada período mensal inclui o ano; não agrupar janeiro de anos diferentes.
Publicar somente meses, dias ISO e horas observados, mais o grupo sem hora
quando existir; não inventar dias abertos, meses vazios ou funcionamento.

Receita mantém a unidade monetária original. Não converter ou rotular USD
como declaração comprovada da fonte. Essa pendência de apresentação não altera
as somas exatas de total/Price nem autoriza alterar os dados.
Os marts representam a janela completa da fonte. Fora do mart mensal, os grãos
propostos não suportam filtros arbitrários de data; filtros futuros exigem
revisão dos grãos e recálculo coerente de denominadores, rankings e Pareto.

### TREZE SAÍDAS E GRÃOS

Nomes de arquivos, tabelas, fontes e fórmulas seguem a tabela completa de
docs/contratos-indicadores.md, linhas 01 a 13. O contrato cobre todos os
indicadores de indicadores.md, sem adicionar indicadores nesta etapa.

05_ticket_por_pedido e 09_quantidade_por_pedido são bases auditáveis, com uma
linha por pedido, não distribuições agregadas. O ticket global fica no 10_kpis.
02 mantém variantes separadas por SKU; 11 consolida tamanhos por Name.
08 usa o mesmo agrupamento de 11, mas calcula concentração. Não somar esses
três conjuntos entre si: são representações das mesmas vendas.

Rankings usam DENSE_RANK por receita DESC, sem desempatar a posição por ID.
Exibição ordena receita DESC e SKU/Name ASC para ser estável.
Pareto usa ordem receita DESC, Name ASC e janela ROWS; o membro do grupo de
80% satisfaz 100 × receita_acumulada_anterior < 80 × receita_total.
Isso inclui a linha que cruza ou atinge 80%, sem usar percentual arredondado.
Percentuais são calculados no SQL para apresentação; corte e reconciliações
usam valores monetários exatos. Total de receita zero impede a publicação.

13 agrupa primeiro por cliente com compras e depois por quantidade de pedidos.
Entregar frequência, quantidade de clientes, percentual desses clientes e
proporção global com mais de um pedido. Denominador: clientes com compra,
não o catálogo inteiro. A proporção global repetida por faixa não é aditiva.

### VALIDAÇÃO ANTES DO COMMIT

Executor confere a presença dos 13 arquivos contratados. Pasta vazia, arquivo
inesperado, prefixo não numérico/duplicado ou arquivo obrigatório faltando falha
antes do DROP. Mudança de inventário exige atualizar spec e testes primeiro.
Recriar o schema remove tabelas antigas extras; não publicar apenas 12 saídas
porque um SQL foi removido por engano.

Além das contagens, verificar grãos únicos, chaves obrigatórias não nulas,
integridade da refined, Name/Category consistente e reconciliação por pedido.
A única dimensão nula permitida é hora no grupo explicitamente identificado
como não informada; não trocar NULL por zero.

Comparar receita mensal/SKU/Name/categoria/tamanho/loja com SUM(orders.total),
exatamente em DECIMAL. Conferir contagens por mês/dia ISO/hora/loja com pedidos,
e unidades por SKU/Name/categoria/tamanho/loja com SUM(nItems), quando expostas.
05 e 09 conferem cada pedido e suas somas; 10 tem exatamente uma linha.
11 reconcilia cada Name com seus SKUs do 02; 08 reconcilia receita com 11,
ordenação/acumulado e prefixo mínimo de 80%, incluindo o produto do corte.
13: soma de clientes = clientes distintos com compra; soma de frequência ×
clientes = pedidos; recompra = clientes com frequência >1 / clientes com compra.
Tickets, médias e proporções são conferidos por numerador/denominador,
sem somar médias. Comparações de razões aceitam erro absoluto até 1e-9;
essa tolerância não se aplica às somas monetárias, que são exatas.
SQLs de construção leem somente refined; auditorias podem comparar marts entre
si, mas nunca construir um mart a partir de outro. Nenhuma fórmula em Python.

## CRITÉRIOS DE ACEITE

Treze saídas não vazias com grãos únicos conforme contrato; reconciliações
financeiras exatas após regra monetária validada. JOIN não perde nem duplica
ocorrências além da fonte. Um pedido com dois itens conta uma vez no ticket.
Duas linhas idênticas de item contam duas unidades. Datas sem hora entram no
grupo próprio. SQL com erro, vazio ou prefixo inválido preserva versão anterior.
Arquivo obrigatório ausente falha antes da escrita; tabelas antigas extras
desaparecem na recriação bem-sucedida. Repetir execução mantém resultado.

## ENTREGA

Specs antes do código; SQLs revisados; executor com docstring; testes sintéticos
DuckDB temporário real, sem rede/dados do projeto; resultados, cobertura e
limitações medidas. Testar empates, repetição legítima de item, dois anos com
mesmo mês, data sem hora, loja/cliente sem compra, corte Pareto exato e cruzado,
receita zero, erro SQL, arquivo ausente e rollback preservando marts anteriores.
Moeda declarada segue pendente; horários usam São Paulo por decisão do usuário,
sem afirmar o fuso comercial das lojas. Não implementar dashboard nesta etapa.
