# Etapa 1B — ingestão dos quatro CSVs

## Arquivos e decisões

Criados pipeline/ingestao.py e test/test_ingestao.py. Atualizados spec prévia,
README e plano. A spec recebeu antes do código o uso de dtype="string" para
garantir VARCHAR em colunas inteiramente nulas e validação estrutural estrita
dos registros. Não há deduplicação ou transformação de valores na RAW.

Todas as fontes são verificadas e lidas antes de abrir o banco. csv.reader
valida cabeçalhos e número de campos, inclusive aspas; pandas lê os valores
com encoding explícito, sem inferência numérica ou lista automática de nulos.
A gravação das quatro tabelas ocorre em uma transação, com rollback em erro,
conexão fechada em finally e logs de sucesso somente após commit.

## Comandos executados e resultados

- `.venv/bin/ruff format pipeline/ingestao.py test/test_ingestao.py`: formatou
  automaticamente os dois arquivos; exceção de edição apenas para layout.
- `.venv/bin/ruff check .`: aprovado.
- `.venv/bin/pytest --cov`: 18 testes passaram em 1,70 s. db.py: 20 linhas,
  100%; ingestao.py: 51 linhas, 98%; total: 71 linhas, 98,59%.
- `.venv/bin/python -m pipeline.ingestao` executado duas vezes com logs em
  /tmp/pizza-ingestao-primeira.txt e /tmp/pizza-ingestao-segunda.txt; `cmp`
  confirmou saídas idênticas.
- `.venv/bin/ruff format --check .`: aprovado.
- Auditoria somente leitura com csv.reader, Counter, hashlib e DuckDB:
  comparou todas as linhas e multiplicidades do banco com os CSVs, conferiu
  VARCHAR em todas as colunas e hashes individuais contra o inventário.
  Todos os asserts passaram; somente schema de dados raw existe.
- `uv run python -m pipeline.ingestao`: comando do README validado com sucesso,
  produzindo as mesmas contagens.

```text
raw.orders         21.350 linhas
raw.order_details  48.620 linhas
raw.pizzas             96 linhas
raw.pizza_types        32 linhas
total              70.098 linhas
```

## Testes e critérios de aceite

Os 11 casos de ingestão, além dos sete de conexão, usam CSVs sintéticos e bancos
reais temporários: preservação de valores, zeros iniciais, duplicatas, espaços,
cp1252, vírgula/quebra de linha entre aspas, tokens NA/N/A/NULL, campo vazio e
coluna inteiramente nula; reexecução; fonte ausente antes de criar banco;
cabeçalho inválido, campos a mais/a menos, linha vazia, aspas inválidas e
encoding inválido. Erro real no último destino restaura tabela anterior e
remove as tabelas criadas pelos passos anteriores da transação.

Critérios atendidos: quatro fontes, 15 colunas VARCHAR, valores e repetições
preservados, total da v1 reconciliado com arquivos, falhas controladas,
idempotência e ausência de atualização parcial. Banco pizza.duckdb foi criado
localmente e continua ignorado pelo Git, assim como as fontes.

## Problemas, suposições e pendências

Nenhuma falha funcional observada nos testes ou carga real. Ruff ajustou apenas
formatação. A única linha Python não coberta pela suíte é sys.exit(main()) na
entrada do módulo; o CLI foi validado em execução real independente.
Não há suposição de negócio adicional; decisões de leitura foram explicitadas
na spec antes de codificar. cp1252 permanece a escolha declarada para a fonte.

AGENTS.md permanece local e foi removido do índice a pedido do usuário; não
apagar ou reescrever commits antigos. Preparar o commit da ingestão após revisar
esta evidência. Próximo passo: investigação/SELECTs da transformação; refined,
marts e dashboard permanecem pendentes.
