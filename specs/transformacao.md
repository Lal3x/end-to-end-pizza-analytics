# Etapa 2 — Transformação Pizza Paradise

Status: contrato proposto após migração autorizada; validar SELECTs na nova RAW
e revisar os resultados antes de implementar pipeline/transformacao.py.
Substitui a proposta da fonte Maven, preservada no histórico.

## CONTEXTO

Tornar os cinco grãos confiáveis sem inventar informação temporal ou perder
unidades repetidas. Evidência prévia: docs/avaliacao-pizza-paradise.md.
Os SELECTs antigos da Maven não se aplicam a esta fonte.

## STACK

Python 3.13, uv e SQL DuckDB local; dinheiro em DECIMAL(18,2).
Sem processamento de fatos completos no pandas.

## O QUE JÁ EXISTE

Aquisição e ingestão migradas, cinco tabelas RAW auditadas integralmente,
26 testes aprovados e fonte anterior preservada. Nenhuma refined existe.
Esta etapa executa somente SELECTs com conexão read_only=True; relatórios
podem ser gravados como arquivos, sem criar tabelas temporárias ou views.

## ARTEFATO A PRODUZIR

pipeline/transformacao.py e SELECTs próprios de transformação, após revisão.
Comando futuro: uv run python -m pipeline.transformacao.

## SPEC

### 1. ESCOPO

Ler raw.orders, raw.order_items, raw.products, raw.customers e raw.stores;
publicar cinco tabelas refined em transação única. Nunca alterar RAW.
Motivo: preservar a fonte e todos os grãos.

### 2. NOMES E TIPOS

Manter nomes originais. Proposta completa por tabela:
- orders: id VARCHAR, customerId VARCHAR, storeId VARCHAR, orderDate VARCHAR
  preservado; nItems INTEGER; total DECIMAL(18,2).
- order_items: SKU VARCHAR e orderID VARCHAR, preservando ocorrências.
- products: SKU/Name/Category/Size/Ingredients VARCHAR; Price DECIMAL(18,2);
  Launch DATE.
- customers: id VARCHAR; latitude/longitude DOUBLE.
- stores: id/zipcode/state_abbr/city/state VARCHAR;
  latitude/longitude/distance DOUBLE.

Em orders acrescentar order_date DATE, order_timestamp TIMESTAMPTZ opcional
e timestamp_precision VARCHAR (second, minute, date).
Motivo: conservar orderDate original e distinguir precisão sem inventar hora.
Aprovar explicitamente as colunas derivadas antes da implementação.
Sem criar ID natural inexistente para order_items.

### 3. CONVERSÕES E ERROS

IDs convertidos semanticamente para texto, dinheiro validado como finito,
não negativo e representável com centavos; conversão de DOUBLE deve verificar
a diferença absoluta entre DOUBLE original e DECIMAL convertido de volta para
DOUBLE: aceitar no máximo 1e-9 unidade monetária, após validar finitude,
não negatividade e representabilidade em DECIMAL(18,2). Acima disso, falhar.
Essa tolerância é dez milhões de vezes menor que um centavo e destina-se apenas
ao ruído binário. Na investigação inicial, o maior desvio foi
2.842170943040401e-14; nenhum valor excedeu 1e-9. Magnitudes novas que não
caibam nessa regra exigem revisão; não alargar a tolerância automaticamente.
Price do CSV deve casar [0-9]+([.][0-9]{1,2})? antes do CAST, sem arredondar
entradas com terceira casa. Motivo: DOUBLE e texto monetário têm representações
diferentes; nenhum centavo adicional real pode ser aceito silenciosamente.
Formato de orderDate: ISO com Z até segundos, com Z até minutos, ou somente
data. Zero formatos desconhecidos aceitos.
Somente data: order_date preenchida, order_timestamp NULL; precisão date.
Minutos: timestamp no início do minuto, precisão minute; não alegar segundos
medidos. Z indica UTC; período comercial local exige decisão própria.
Motivo: distinguir ausência de hora de meia-noite verdadeira.

### 4. CORREÇÃO CONTROLADA DE LAUNCH

PZ026 e PZ027 possuem 2020-01-01, na fonte inspecionada. Proposta: remover
somente uma vírgula terminal quando o restante casar exatamente YYYY-MM-DD;
converter estritamente, exibir valor original/corrigido e contagem.
Não fazer strip genérico ou aceitar outros sufixos; nova irregularidade falha.
Motivo: corrigir anomalia demonstrada sem generalizar uma limpeza arbitrária.
Esta correção requer revisão dos resultados antes de implementação.

### 5. CHAVES E REPETIÇÕES

PKs: orders.id, customers.id, stores.id, products.SKU.
Nessas quatro, remover apenas duplicatas exatas com contagem; conflitos falham.
order_items não tem PK de linha: preservar todas as ocorrências, inclusive
pares (orderID, SKU) idênticos. Não aplicar DISTINCT.
Motivo: há itens iguais no mesmo pedido e removê-los reduz vendas legítimas.
Não usar um hash só de orderID/SKU como chave única.
Se for necessário identificar ocorrências, propor contrato específico.

### 6. NULOS, DOMÍNIOS E RELAÇÕES

Nulos obrigatórios/IDs vazios falham; Ingredients pode ser nulo, sem preenchimento.
order_timestamp nulo é permitido exclusivamente quando a precisão é date.
Validar quatro FKs; nItems inteiro positivo, preços/totais não negativos e
coordenadas finitas dentro de limites válidos.
distance é preservada; unidade e significado ainda não comprovados.
Domínios de Size/Category observados no modelo não justificam excluir valores
novos: revisar domínio e falhar explicitamente, nunca filtrar em silêncio.
Reconciliações: COUNT de ocorrências por pedido = nItems e soma Price dos
itens = total, após regra monetária validada, em cada pedido.
Motivo: consistência medida por caminhos independentes.

### 7. SAÍDA NA TELA

Antes/depois por tabela: linhas, nulos, tipos, repetições removidas ou
preservadas; formatos temporais e correções Launch. Contagens do banco,
stdout UTF-8. Exibir exemplos das mudanças sem transformar a RAW.

## REEXECUÇÃO E ERRO

Recriação idempotente em transação única; validar entradas, conversões,
conflitos, relações e reconciliações antes de COMMIT.
Qualquer falha identifica tabela/coluna/exemplo e preserva refined anterior.
TRY_* só para diagnóstico que rejeita falhas; não para ocultar erros.

## CRITÉRIOS DE ACEITE

As cinco contagens reconciliam com RAW menos duplicatas exatas permitidas nas
quatro tabelas com PK; order_items mantém todas as ocorrências.
Todos os formatos de data classificados; data sem hora não vira meia-noite.
IDs texto, dinheiro DECIMAL e quatro FKs válidas.
Repetições legítimas conservam nItems e receita por pedido.
Erro de conversão, conflito ou diferença financeira gera rollback.
Testes sintéticos cobrem as regras; nenhuma contagem real é teste unitário.

## ENTREGA

SELECTs de investigação na nova RAW e resultados para revisão antes do código.
Depois da aprovação: módulo, testes sintéticos, execução e logs reais.
Pendentes antes de implementar: regra monetária final, colunas temporais
derivadas, correção Launch e interpretação do período/fuso.
