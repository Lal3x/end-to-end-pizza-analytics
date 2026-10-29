# Etapa 1 — Ingestão Pizza Paradise

Status: migração autorizada; este contrato substitui o da fonte Maven.
O histórico anterior permanece nos commits e registros de execução.

## CONTEXTO

Espelhar os cinco arquivos oficiais do Pizza Paradise, versão 398 do notebook,
em raw no banco pizza.duckdb. Esta spec precede a implementação da migração.
Não aplicar regras de limpeza na origem.

## STACK

Python 3.13, uv, pandas para CSV, DuckDB para Parquet e persistência local.
Sem biblioteca, banco ou orquestrador adicional.

## O QUE JÁ EXISTE (use, não reimplemente)

db.py na raiz, ingestão Maven validada e evidência de inspeção do novo conjunto
em docs/evidencias/pizza-paradise-inspecao.json. Antes de substituir a carga
antiga, guardar cópia íntegra do banco e manter os CSVs anteriores.
A aquisição dos anexos deve ser reproduzível e separada da ingestão.

## ARTEFATOS A PRODUZIR

baixar_dados.py na raiz e pipeline/ingestao.py.
Mapa de arquivos/colunas/tipos na ingestão; URLs/hashes somente no downloader.
Não criar módulos de aquisição ou configuração dentro de pipeline/.
Conexão compartilhada em db.py na raiz; pipeline/ fica para as etapas.
Comandos: uv run python baixar_dados.py;
uv run python -m pipeline.ingestao.
O executor aceita --banco para validar uma carga em arquivo separado.
Na execução completa, executar(banco=None, *, con=None) recebe a conexão de
destino com transação ativa; não confirma/reverte/fecha a conexão externa.
Sem con, mantém sua transação e fechamento próprios. banco/con juntos falham.
validar_fontes() pré-valida arquivos sem abrir destino e retorna os CSVs textuais,
reutilizada pelo executor completo conforme specs/execucao-pipeline.md.

## SPEC

### 1. ESCOPO E NOMES

Arquivos em raw/pizza_paradise/:
- customers.csv → raw.customers: id, latitude, longitude.
- stores.csv → raw.stores: id, zipcode, state_abbr, latitude, longitude, city,
  state, distance.
- products.csv → raw.products: SKU, Name, Price, Category, Size, Ingredients,
  Launch.
- orders.parquet → raw.orders: id, customerId, storeId, orderDate, nItems, total.
- order_items.parquet → raw.order_items: SKU, orderID.

Motivo: preservar nomes, inclusive maiúsculas, e usar apenas dados granulares,
não os agregados prontos do notebook.

### 2. PROIBIÇÕES E TIPOS DA RAW

CSV: ler UTF-8 com suporte a BOM, vírgula e aspas duplas, tudo VARCHAR.
Campos vazios viram NULL; NA, N/A e NULL literais permanecem texto.
Parquet: preservar tipos nativos e valores, inclusive DOUBLE de total,
INTEGER dos IDs e todas as ocorrências de itens. Nenhum CAST na ingestão.
Esperados em orders: INTEGER, VARCHAR, VARCHAR, VARCHAR, INTEGER, DOUBLE;
em order_items: VARCHAR, INTEGER, na ordem das colunas acima.
Nunca converter datas, dinheiro ou IDs, deduplicar, normalizar ou descartar
linhas. Motivo: Parquet já é tipado; convertê-lo para texto mudaria sua
representação. A migração autoriza esta diferença do antigo contrato CSV.

### 3. REEXECUÇÃO

Recriar somente raw em transação única, incluindo DROP SCHEMA raw CASCADE,
para remover tabelas da fonte anterior. Não escrever em refined/marts.
Como os grãos da nova fonte são diferentes, recusar executar se refined ou
marts contiverem tabelas; exigir plano explícito para não deixar camadas antigas.
Na primeira migração real, comparar a cópia de segurança com o banco antigo
por SHA-256. Nenhum arquivo de fonte anterior será apagado.
Motivo: evitar mistura de fontes e preservar possibilidade de retorno.

### 4. LEITURA DO ARQUIVO

Verificar os cinco arquivos antes de abrir/criar o banco de destino.
Validar cabeçalhos e estrutura de cada CSV com csv.reader estrito; não pular
linhas vazias ou campos excedentes. Validar colunas e tipos dos Parquets com
conexão DuckDB em memória, sem carregar milhões de linhas no pandas.
Encoding UTF-8 explícito, BOM aceito; fontes não são alteradas na leitura.
Motivo: erro de fonte não pode criar banco vazio ou iniciar carga parcial.

### 5. TIPAGEM

Somente os três CSVs pequenos passam por pandas, dtype="string".
Os dois Parquets são lidos diretamente por DuckDB via read_parquet e CTAS.
Não fazer merge/groupby no pandas nem concatenar os milhões de itens.
Usar parâmetros para caminhos e nomes de tabela delimitados.
Motivo: volume maior sem trazer o fato completo à memória Python.

#### 5.1. AQUISIÇÃO (apoio separado em baixar_dados.py)

URLs de anexos e hashes fixos da versão investigada no script de aquisição.
Aceitar gzip de transporte e descomprimir para conteúdo CSV canônico; validar
SHA-256 do conteúdo antes de publicar os cinco arquivos. Manter respostas
originais e manifesto em data/pizza_paradise/. Aquisição usa área temporária
e só publica o diretório completo após validar todos os anexos.
Se fontes já existentes tiverem conteúdo diferente, falhar sem sobrescrever.
Motivo: URLs, compressão e integridade precisam ser reproduzíveis.

### 6. SAÍDA NA TELA

Contagem de cada tabela consultada no banco e total após COMMIT; stdout UTF-8.
Uma linha por tabela com nome qualificado e milhar separado por ponto; linha
final com total. Motivo: anunciar somente uma carga publicada.

### 7. ERRO

Fonte ausente/inválida: nome, caminho e causa; saída 1. SQL inválido: rollback;
não imprimir sucesso parcial. Sempre fechar conexões.
Falha de aquisição não autoriza substituir fontes por dados inventados.

## CRITÉRIOS DE ACEITE

Na versão inspecionada: orders 2.046.713; order_items 2.916.015;
customers 34.761; stores 32; products 36; total 4.997.557.
Estes são resultados de referência da versão, não limites de crescimento.
Duas cargas mantêm valores, multiplicidades, tipos e contagens.
As 54.041 ocorrências repetidas além da primeira em order_items permanecem.
Ausência, CSV inválido e Parquet inválido falham antes de modificar o destino.
Erro durante a transação preserva a camada anterior.
Os testes não usam rede, fontes reais nem o banco do projeto.

## ENTREGA

Spec antes do código; testes sintéticos com Parquet e DuckDB reais temporários;
carga em banco separado, auditoria integral e duas execuções; cópia do banco
anterior; registro de tempos/resultados medidos e suposições.
Não implementar transformação ou marts neste incremento.
