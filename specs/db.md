# Etapa 1 — Módulo de conexão

Status: implementação autorizada após revisão da Etapa Zero; validar antes da
ingestão. Fundação registrada no commit fd85358.

## CONTEXTO

Preparar acesso comum ao DuckDB sem esconder regras de negócio. Esta spec
precede código e é dependência da ingestão.

## STACK

Python 3.13, uv, DuckDB local e pandas para o DataFrame a gravar.

## O QUE JÁ EXISTE (use, não reimplemente)

Ambiente/configurações e CSVs locais. Ainda não há `pizza.duckdb` ou `pipeline/`.
Cada etapa decide suas colunas/tipos, não o módulo comum.

## ARTEFATO A PRODUZIR

`pipeline/db.py`, expondo somente:

```text
PASTA_RAW                        Path de raw/ na raiz
conectar()                       abre pizza.duckdb, criando se faltar
criar_schema(con, nome)          cria schema se não existir
gravar(con, df, schema, tabela)   substitui tabela e retorna count(*) do banco
```

## SPEC

### D1. CAMINHOS

Resolver raw/ e pizza.duckdb pela localização do módulo, nunca pelo diretório
corrente. Motivo: executar de outra pasta não pode criar banco no lugar errado.

### D2. RESPONSABILIDADES E PROIBIÇÕES

Não ler CSV, conhecer tabelas de negócio, imprimir, converter, deduplicar ou
filtrar. Importar não abre conexão nem cria arquivo. Sem conexão global.
Motivo: infraestrutura comum não decide regras de todas as etapas.

### D3. GRAVAR

`CREATE OR REPLACE TABLE` com colunas/tipos do DataFrame e nulos preservados;
texto vira VARCHAR. Retornar contagem da tabela final. Sem views ou tabelas
temporárias remanescentes e sem commit da transação do chamador.
Motivo: cada etapa controla sua transação e confere o que gravou.

Registrar o DataFrame sob um nome temporário exclusivo e remover esse registro
em finally, inclusive se a gravação falhar. Delimitar identificadores SQL com
aspas duplas e escapar aspas internas; não interpolar nomes como SQL executável.
Motivo: registros não podem vazar, colidir ou interpretar nomes como comandos.

### D4. CONEXÃO E ERRO

Devolver conexão aberta; quem chama fecha. Propagar erros para a etapa emitir
mensagem, rollback e saída 1; não consumir exceção. Motivo: o módulo não conhece
qual fonte/regra de negócio falhou.

## CRITÉRIOS DE ACEITE

- Importar não cria banco; executar de outra pasta ainda usa a raiz configurada.
- DataFrame sintético de três linhas retorna 3; regravar mantém 3.
- Zero inicial, nulo e tipos preservados.
- Falha de gravação propaga erro e remove o registro temporário do DataFrame.
- Rollback do chamador desfaz gravação; fechar libera conexão.
- Testes usam monkeypatch para redirecionar caminhos a tmp_path e DuckDB real;
  nunca abrem banco/CSV do projeto.

## ENTREGA

1. Módulo com docstring referenciando esta spec e seus motivos.
2. Testes em `test/test_db.py` com DuckDB temporário real.
3. Resultados dos critérios e suposições não previstas.
