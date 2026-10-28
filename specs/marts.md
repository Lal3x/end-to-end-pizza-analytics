# Etapa 3 — Executor de marts

Status: proposta para revisão; não implementar na Etapa Zero.

## CONTEXTO

Estou construindo um pipeline de vendas de pizzaria com spec-driven development.
Este módulo executa SQLs já definidos/revisados. Contratos de cada pergunta:
[docs/contratos-indicadores.md](../docs/contratos-indicadores.md). Não inventar
fórmulas no executor nem introduzir regras implícitas.

## STACK

- Python 3.13, uv e DuckDB local em `pizza.duckdb`.
- SQL DuckDB em arquivos numerados; nenhum orquestrador.

## O QUE JÁ EXISTE (use, não reimplemente)

Existem fontes, inventário, ambiente e documentos. Ainda não há banco, refined,
módulo de conexão ou SQLs de marts.

Pré-condições futuras: `pipeline/db.py` validado, quatro refined validadas e
`sql/marts/NN_nome.sql` revisados. Cada arquivo contém um SELECT, podendo começar
com comentários e WITH. O executor vem depois dos SQLs.

## ARTEFATO A PRODUZIR

`pipeline/marts.py`, futuramente executável com:

```bash
uv run python -m pipeline.marts
```

## SPEC

### 1. ESCOPO

Ler refined, escrever somente marts. Recriar schema a cada execução com
`DROP SCHEMA IF EXISTS marts CASCADE` e criação, dentro da transação.
Motivo: SQL removido não pode deixar indicador antigo no banco.

### 2. UM ARQUIVO, UMA TABELA

Ler `sql/marts/*.sql` em ordem alfabética, prefixo `NN_`. Tabela = nome do
arquivo sem extensão/prefixo:

```text
sql/marts/01_vendas_mensais.sql -> marts.vendas_mensais
```

Executar `CREATE TABLE marts.<nome> AS <conteúdo do arquivo>`; remover apenas
espaços e um ponto e vírgula final. Não alterar/completar/montar fórmulas.
Motivo: toda regra permanece rastreável no SQL da pergunta.

Cada SQL declara pergunta e grão no comentário inicial, grão de cada CTE e lê
apenas refined. Contratos candidatos estão no documento analítico; seleção
final será revisada antes do SQL.

### 3. SAÍDA NA TELA

stdout UTF-8; uma linha por mart com contagem do banco, milhar com ponto; total
de marts e linhas ao fim. Não anunciar sucesso antes do commit da transação.
Não há contagens de marts reais medidas ainda.
Motivo: log de sucesso deve descrever tabelas publicadas, não versões parciais.

### 4. ERRO

Antes de escrever, verificar quatro tabelas refined e pasta SQL. Tabela ausente:
listar e orientar `uv run python -m pipeline.transformacao`; saída 1. Sem SQL,
prefixo inválido ou nomes duplicados: listar e sair antes de executar arquivos.

SQL falhou: nome do arquivo/mensagem DuckDB, sem executar os seguintes. Mart
obrigatório vazio: falha explícita. Toda operação, incluindo DROP do schema,
fica em uma transação; falha restaura última versão válida. Fechar conexão e
saída 1. Motivo: uma camada parcial não pode chegar ao dashboard.

### 5. VALIDAÇÃO DOS INDICADORES

Executar verificações SQL independentes antes de publicar, sem fórmulas Python:

- Grãos únicos e JOINs N:1 preservando linhas/IDs dos itens.
- Receita mensal = categoria = tipo = tamanho = soma por pedido = KPI,
  sem diferença de centavos.
- Ranking principal 02 por pizza_id, separando tamanhos; ranking adicional 11
  por pizza_type_id, consolidando tamanhos. Ambos reconciliam com a receita
  total; a soma das variantes de cada tipo no 02 coincide com o valor no 11.
  Nunca somar os totais dos dois rankings entre si.
- Pedidos mensais = dia da semana = hora = quantidade de pedidos nas saídas
  por pedido = KPI.
- Unidades por tamanho = soma das unidades por pedido = KPI.
- Pareto por tipo: acumulado não decrescente e final 100%; grupo de 80% inclui
  o tipo que alcança/ultrapassa o limite. Quantidade e percentual dos tipos do
  grupo são calculados no SQL sobre os tipos com vendas, sem presumir relação
  80/20. Comparar o corte antes de arredondar percentuais.

Receita zero impede concentração: falhar com diagnóstico até revisão, nunca
dividir por zero. Dinheiro DECIMAL, quantity × price antes de agregar e receita
por pedido antes da média. Sem média de médias ou soma de tickets.
Motivo: caminhos independentes detectam erro de grão e população.

## CRITÉRIOS DE ACEITE

- Em banco temporário com dependências válidas, `00_teste.sql` com
  `SELECT 1 AS x` cria marts.teste com uma linha.
- Apagar esse arquivo e reexecutar remove marts.teste.
- `teste.sql` sem prefixo e dois arquivos com mesmo nome de saída falham antes
  de modificar marts.
- Falha no segundo SQL ou mart vazio preserva tabelas/valores anteriores.
- Duas execuções produzem mesmos dados/saída, com desempate estável nas janelas.
- SQLs de negócio passam no item 5; esse aceite é separado do teste de
  encanamento `SELECT 1`.
- Exemplo com um pedido e dois itens conta um pedido no ticket, multiplica
  quantidade por preço e conserva grão em cada JOIN N:1.

## ENTREGA

1. Após revisão dos indicadores, SQLs com pergunta, fontes, grãos e regras.
2. Executor com docstring referenciando spec, regras e motivos.
3. Testes sintéticos com DuckDB real, inclusive rollback/idempotência.
4. Resultados das verificações SQL independentes.
5. Suposições não previstas e critérios atendidos/pendentes.
