# Etapa 2 — Transformação Pizza Paradise

Status: contrato aprovado pelo usuário em 28/10/2026 e implementado com pandas
em um único módulo, pipeline/transformacao.py. Execução real documentada em
docs/execucao-transformacao.md.

## CONTEXTO

Tornar os cinco grãos confiáveis sem inventar informação temporal ou perder
unidades repetidas. Evidência prévia: docs/avaliacao-pizza-paradise.md.

## STACK

Python 3.13, uv, pandas para transformar e DuckDB para ler/gravar.
Dinheiro com decimal.Decimal no DataFrame e DECIMAL(18,2) no destino.

## O QUE JÁ EXISTE

Aquisição e ingestão implementadas, cinco tabelas RAW auditadas integralmente
e 26 testes aprovados antes desta etapa.
Na conclusão: cinco refined publicadas, 61 testes e cobertura 94,12%.
A investigação SQL anterior está documentada como histórico. Ela não será
o mecanismo da transformação: o usuário corrigiu o escopo para usar pandas.

## ARTEFATO A PRODUZIR

pipeline/transformacao.py, com funções pandas explícitas e testes sintéticos.
Não criar executor de arquivos SQL de transformação ou módulos adicionais de
regras. SQL analítico fica nos marts, executado por pipeline/marts.py.
Comando: uv run python -m pipeline.transformacao.
Integração: executar(banco=None, *, con=None) aceita a transação externa do
executor completo; nessa modalidade não inicia/confirma/reverte/fecha a conexão.
Sem con, mantém o comportamento isolado. banco/con juntos são inválidos.
Contrato de composição: specs/execucao-pipeline.md.

## SPEC

### 1. ESCOPO

Ler raw.orders, raw.order_items, raw.products, raw.customers e raw.stores;
publicar cinco tabelas refined em transação única. Nunca alterar RAW.
Motivo: preservar a fonte e todos os grãos.

Ler e transformar uma tabela por vez em DataFrame; não manter cinco tabelas
ou JOINs completos simultaneamente. Usar db.py para persistência sob transação
controlada pela etapa. Medir tempo e memória antes de afirmar desempenho.
Não adicionar lotes ou abstrações sem demonstrar necessidade e especificar
suas regras, inclusive deduplicação/conflitos entre lotes.

### 2. NOMES

Manter nomes originais, sem renomear ou descartar colunas. Acrescentar somente
order_date, order_timestamp e timestamp_precision em orders, conforme aprovação.
Motivo: manter rastreabilidade da representação original.

### 3. TIPOS

Mapa completo aprovado por tabela:
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
Colunas derivadas aprovadas explicitamente pelo usuário.
Sem criar ID natural inexistente para order_items.

### 4. CONVERSÃO QUE FALHA

Para tudo; nunca transformar erro de conversão em nulo. Identificar tabela,
coluna e exemplo; rollback e saída 1. Motivo: distinguir erro de nulo da fonte.

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
No pandas, validar strings antes de converter; usar Decimal a partir do texto,
quantizando centavos de total somente sob a tolerância definida. Verificar o
tipo DECIMAL do resultado persistido. Não usar float como resultado monetário.
Na fronteira com DuckDB, transportar Decimal como string exata e declarar
DECIMAL(18,2) na mesma transação, evitando a inferência por amostra de objetos
Decimal. A conversão e validação financeira continuam integralmente pandas.
Formato de orderDate: ISO com Z até segundos, com Z até minutos, ou somente
data. Zero formatos desconhecidos aceitos.
Somente data: order_date preenchida, order_timestamp NULL; precisão date.
Minutos: timestamp no início do minuto, precisão minute; não alegar segundos
medidos. Z indica UTC; período comercial local exige decisão própria.
Motivo: distinguir ausência de hora de meia-noite verdadeira. No pandas,
classificar formatos por máscaras explícitas e usar pd.to_datetime com formato
declarado, errors='raise' e utc=True onde houver Z. Não usar errors='coerce'.

#### 4.1. CORREÇÃO CONTROLADA DE LAUNCH

PZ026 e PZ027 possuem 2020-01-01, na fonte inspecionada. Regra aprovada: remover
somente uma vírgula terminal quando o restante casar exatamente YYYY-MM-DD;
converter estritamente, exibir valor original/corrigido e contagem.
Não fazer strip genérico ou aceitar outros sufixos; nova irregularidade falha.
Aplicar correção por máscara pandas e converter com formato declarado.
Motivo: corrigir anomalia demonstrada sem generalizar uma limpeza arbitrária.
Esta correção foi aprovada explicitamente pelo usuário.

### 5. DUPLICATAS

PKs: orders.id, customers.id, stores.id, products.SKU.
Nessas quatro, verificar conflitos com pandas antes de gravar; remover apenas
duplicatas exatas com drop_duplicates e contagem. Conflitos falham.
order_items não tem PK de linha: preservar todas as ocorrências, inclusive
pares (orderID, SKU) idênticos. Não aplicar drop_duplicates nessa tabela.
Motivo: há itens iguais no mesmo pedido e removê-los reduz vendas legítimas.
Não usar um hash só de orderID/SKU como chave única.
Se for necessário identificar ocorrências, propor contrato específico.

### 6. NULOS

Nulos obrigatórios/IDs vazios falham; Ingredients pode ser nulo, sem preenchimento.
order_timestamp nulo é permitido exclusivamente quando a precisão é date.
Validar quatro FKs; nItems inteiro positivo, preços/totais não negativos e
coordenadas finitas dentro de limites válidos.
distance é preservada; unidade e significado ainda não comprovados.
Domínios de Size/Category observados no modelo não justificam excluir valores
novos: revisar domínio e falhar explicitamente, nunca filtrar em silêncio.
Domínios atuais: Size = Small, Medium, Large, Extra Large; Category = Classic,
Vegetarian, Specialty. Tabelas vazias ou colunas fora do contrato falham.
Reconciliações: COUNT de ocorrências por pedido = nItems e soma Price dos
itens = total, após regra monetária validada, em cada pedido.
Motivo: consistência medida por caminhos independentes.
As conversões e deduplicações são pandas. Após persistir na transação,
auditar FKs e reconciliações com consultas SQL independentes, sem usá-las para
transformar a fonte. SQL também declara os tipos físicos monetários do destino.

### 7. SAÍDA NA TELA

Antes/depois por tabela: linhas, nulos, tipos, repetições removidas ou
preservadas; formatos temporais e correções Launch. Contagens do banco,
stdout UTF-8. Exibir exemplos das mudanças sem transformar a RAW.

## REEXECUÇÃO E ERRO

Recriação idempotente em transação única; validar entradas, conversões,
conflitos, relações e reconciliações antes de COMMIT.
Qualquer falha identifica tabela/coluna/exemplo e preserva refined anterior.
Conversões pandas com errors='raise'; não usar errors='coerce' ou preencher
falhas de conversão como se fossem nulos da fonte.

## CRITÉRIOS DE ACEITE

As cinco contagens reconciliam com RAW menos duplicatas exatas permitidas nas
quatro tabelas com PK; order_items mantém todas as ocorrências.
Todos os formatos de data classificados; data sem hora não vira meia-noite.
IDs texto, dinheiro DECIMAL e quatro FKs válidas.
Repetições legítimas conservam nItems e receita por pedido.
Erro de conversão, conflito ou diferença financeira gera rollback.
Testes sintéticos cobrem as regras; nenhuma contagem real é teste unitário.

## ENTREGA

Investigação prévia em docs/validacao-refined.md, sem usar seus SQLs como
implementação. Revisar este contrato pandas antes do código. Depois: módulo,
testes sintéticos, execução e logs reais.
Regra monetária, colunas temporais e correção Launch aprovadas explicitamente.
Horários com Z permanecem em UTC na refined. A revisão de 29/10/2026 aplica
America/Sao_Paulo somente ao mart horário; não altera a transformação nem
afirma o fuso comercial das lojas. Resultados medidos ficam em docs/.
