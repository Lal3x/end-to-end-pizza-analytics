# Etapa 1 — Ingestão

Status: proposta para revisão; implementar somente após revisão da Etapa Zero.

## CONTEXTO

Estou construindo um pipeline de vendas de pizzaria com spec-driven development.
Esta spec é o contrato anterior ao código. O objetivo é espelhar as quatro
fontes em raw sem mudar seus valores. Não acrescente regras implícitas;
registre ambiguidades antes de implementar.

## STACK

- Python 3.13, dependências gerenciadas com uv.
- pandas para ler os CSVs; DuckDB local em `pizza.duckdb`.
- Script de linha de comando; nenhum orquestrador ou serviço adicional.

## O QUE JÁ EXISTE (use, não reimplemente)

- `raw/` com quatro fontes e `data_dictionary.csv`, preservados como baixados.
- Ambiente, `pyproject.toml` e `uv.lock` validados.
- `docs/evidencias/inspecao.json` com contagens/hashes e `docs/modelo.md`.

`pipeline/db.py` está implementado e validado conforme [db.md](db.md), expondo
PASTA_RAW, conectar(), criar_schema() e gravar(). O banco do projeto ainda não
foi criado. Reutilizar o módulo; não reimplementar suas funções na ingestão.

## ARTEFATO A PRODUZIR

`pipeline/ingestao.py`, executável na futura etapa autorizada com:

```bash
uv run python -m pipeline.ingestao
```

## SPEC

### 1. ESCOPO E NOMES

Schema: `raw`. Mapa completo e literal:

```text
orders.csv        -> raw.orders
order_details.csv -> raw.order_details
pizzas.csv        -> raw.pizzas
pizza_types.csv   -> raw.pizza_types
```

Manter os cabeçalhos de docs/modelo.md. O dicionário é metadado local, não uma
quinta tabela obrigatória de vendas. Motivo: rastrear nomes até a fonte.

### 2. PROIBIÇÕES

Nenhuma conversão, deduplicação, remoção de linha, renomeação, preenchimento
de nulo ou normalização de espaços/acentos. Não escrever nos CSVs, refined ou
marts. Motivo: toda mudança do dado pertence à transformação.

### 3. REEXECUÇÃO

Recriar tabelas com `CREATE OR REPLACE`, nunca acrescentar. As quatro gravações
ficam em uma transação. Motivo: reexecutar não pode duplicar nem misturar versões.

### 4. LEITURA DO ARQUIVO

CSV com vírgula e aspas duplas; encoding declarado por arquivo:

```text
orders.csv        utf-8-sig
order_details.csv utf-8-sig
pizzas.csv        utf-8-sig
pizza_types.csv   cp1252
```

Campo vazio vira NULL; textos `NA`, `N/A` e `NULL` permanecem texto. Desligar a
lista automática ampla de nulos do pandas. Encoding inválido falha; não ignorar
ou substituir bytes. cp1252 é proposta compatível com os bytes observados.
Motivo: UTF-8 falhou em pizza_types e os defaults de leitura podem mudar valores.

### 5. TIPAGEM

Todas as colunas como texto (`dtype=str`), inferência desligada, nulos como
NULL no banco. As 15 colunas serão VARCHAR. Motivo: números, IDs e datas não
devem ser interpretados silenciosamente na camada de origem.

### 6. SAÍDA NA TELA

stdout UTF-8; uma linha por tabela, nome qualificado e contagem consultada no
banco, milhar com ponto; total no fim. Referência medida no CSV da v1, ainda
não resultado de ingestão:

```text
raw.orders         21.350 linhas
raw.order_details  48.620 linhas
raw.pizzas             96 linhas
raw.pizza_types        32 linhas
total              70.098 linhas
```

Motivo: comparar a fonte com o que foi efetivamente gravado.

### 7. ERRO

Verificar todos os arquivos antes de abrir/criar o banco; antes de gravar,
validar cabeçalhos e estrutura CSV. Fonte ausente: listar arquivos/pasta e
`sys.exit(1)`. CSV, encoding ou banco inválido: fonte/causa, rollback e saída 1.
Não continuar parcialmente; fechar conexão. Motivo: uma carga incompleta não
pode parecer válida.

## CRITÉRIOS DE ACEITE

- Na v1 do inventário: quatro tabelas, contagens acima e total 70.098;
  não usar esses números para rejeitar automaticamente uma nova versão.
- Todas as colunas VARCHAR, mesmos valores e quantidade de linhas da fonte.
- Duas execuções consecutivas têm mesmos dados e mesma saída.
- Fonte ausente impede qualquer gravação e identifica o arquivo.
- CSV sintético preserva zero inicial, cp1252, NULL de vazio e `NA` literal.
- Falha preserva raw anterior; processo fecha conexão e devolve o terminal.

## ENTREGA

1. Módulo com docstring referenciando esta spec, regras e motivos.
2. Código com comentários nas decisões não óbvias.
3. Testes em `test/` com CSV sintético e DuckDB temporário real.
4. Comandos, contagens reais, comparação com fonte e reexecução.
5. Suposições não previstas e critérios atendidos/pendentes.
