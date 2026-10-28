# Etapa 2 — Transformação

Status: proposta para revisão; não implementar na Etapa Zero.

## CONTEXTO

Estou construindo um pipeline de vendas de pizzaria com spec-driven development.
O objetivo é tipar e validar sem mudar significado. Antes de gerar código,
revisar esta proposta contra raw. A investigação atual dos CSVs está em
docs/modelo.md e docs/evidencias/inspecao.json.

## STACK

- Python 3.13, uv e DuckDB local em `pizza.duckdb`.
- Conversões em SQL DuckDB, disparadas pelo Python; dinheiro DECIMAL.
- Nenhum serviço ou orquestrador adicional.

## O QUE JÁ EXISTE (use, não reimplemente)

Existem CSVs, inventário, modelo proposto e ambiente. Ainda não existem banco,
raw ou `pipeline/db.py`. Pré-condições futuras: ingestão validada e módulo
com `conectar()` e `criar_schema()`. Reutilizar esse módulo quando estiver pronto.

## ARTEFATO A PRODUZIR

`pipeline/transformacao.py`, futuramente executável com:

```bash
uv run python -m pipeline.transformacao
```

## SPEC

### 1. ESCOPO

Ler orders, order_details, pizzas e pizza_types em raw; escrever as quatro em
refined. Nunca escrever em raw ou marts. Dicionário fora: é metadado, não
tabela analítica. Motivo: preservar fonte e os quatro grãos documentados.

### 2. NOMES

Manter todos os nomes originais, sem descartar coluna:

```text
orders:        order_id, date, time
order_details: order_details_id, order_id, pizza_id, quantity
pizzas:        pizza_id, pizza_type_id, size, price
pizza_types:   pizza_type_id, name, category, ingredients
```

Motivo: dicionário e indicadores usam esse vocabulário.

### 3. TIPOS

Mapa completo, sem inferência:

```text
orders.order_id                 VARCHAR
orders.date                     DATE             formato %d/%m/%Y
orders.time                     TIME             formato %H:%M:%S
order_details.order_details_id  VARCHAR
order_details.order_id          VARCHAR
order_details.pizza_id          VARCHAR
order_details.quantity          INTEGER
pizzas.pizza_id                 VARCHAR
pizzas.pizza_type_id            VARCHAR
pizzas.size                     VARCHAR
pizzas.price                    DECIMAL(10,2)
pizza_types.pizza_type_id        VARCHAR
pizza_types.name                VARCHAR
pizza_types.category            VARCHAR
pizza_types.ingredients         VARCHAR
```

Motivos: datas reais usam dia/mês/ano; fuso não foi declarado; dinheiro exige
centavos exatos; quantidade é contagem e IDs não são medidas. Antes do CAST,
validar quantidade inteira positiva e preço finito, não negativo, na precisão
e com no máximo duas casas. Motivo: CAST não pode arredondar entrada inválida.

### 4. CONVERSÃO QUE FALHA

Parar, mostrar tabela/coluna/exemplo inválido e encerrar com saída 1. Usar
conversões estritas. Não usar `errors=coerce` ou TRY_CAST para aceitar falhas
como nulos; try_* só em diagnóstico que conte e rejeite falhas.
Motivo: nulo fabricado não pode ser confundido com ausência na origem.

### 5. DUPLICATAS

```text
orders        PK (order_id)
order_details PK (order_details_id)
pizzas        PK (pizza_id)
pizza_types   PK (pizza_type_id)
```

Linha inteira repetida: manter uma, informar quantas saíram. Mesma chave com
conteúdo diferente: parar, mostrar chave/linhas conflitantes e saída 1. Validar
conflitos antes de remover repetições exatas. Na v1: zero duplicatas medidas.
Motivo: repetição exata não acrescenta fato; escolher conflito inventa decisão.
Remover somente duplicatas exatas e falhar em conflitos foi aprovado pelo
usuário; isso não autoriza implementar antes da revisão completa da Etapa Zero.

### 6. NULOS E INTEGRIDADE

Nenhum nulo é preenchido; nenhuma linha sai por ter nulo. Ingredients nulo
permanece nulo; em todas as outras colunas, nulo impede publicar refined.
Motivo: são campos necessários para identidade/relação/indicadores, sem regra
de substituição aprovada; ingredients é descrição opcional.

Validar as três FKs do modelo e domínios de quantidade/preço. Categoria/tamanho
novo exige revisar o domínio, não excluir. Não explodir ingredients em linhas.
Motivo: relação inválida pode perder venda; explodir ingredientes muda o grão.

### 7. SAÍDA NA TELA

stdout UTF-8. Por tabela: linhas antes/depois e duplicatas removidas; abaixo,
nulos por coluna antes/depois, tipos antes/depois e exemplos de conversão.
Contagens do banco, milhar com ponto, total no fim. Referência CSV da v1:

```text
refined.orders         21.350 -> 21.350 linhas (0 duplicatas)
refined.order_details  48.620 -> 48.620 linhas (0 duplicatas)
refined.pizzas             96 ->     96 linhas (0 duplicatas)
refined.pizza_types        32 ->     32 linhas (0 duplicatas)
```

Motivo: toda mudança precisa ser visível, não apenas o sucesso da execução.

## REEXECUÇÃO E ERRO

`CREATE OR REPLACE`, nunca acrescentar; transação única. Tabela raw ausente:
listar, orientar `uv run python -m pipeline.ingestao` e saída 1. Tabela vazia,
conflito, conversão, FK ou domínio inválido: diagnóstico, rollback e saída 1.
Fechar conexão sempre. Motivo: preservar refined anterior e nunca alterar raw.

## CRITÉRIOS DE ACEITE

- Na v1: mesmas quatro contagens acima, zero duplicatas removidas, zero nulos
  antes/depois; total 70.098. Em nova fonte: saída = entrada − repetições exatas.
- Catálogo DuckDB mostra os 15 tipos do mapa; IDs conservam valores/zeros iniciais.
- `31/12/2015` vira DATE `2015-12-31`; hora conserva valor e preço conserva centavos.
- Entrada com terceira casa não é arredondada silenciosamente.
- Valor inválido, conflito ou FK órfã falha e preserva refined anterior.
- Repetição exata sai uma vez com contagem explícita; ingredients nulo permanece.
- Duas execuções têm mesmos dados/logs; raw permanece intacta.

## ENTREGA

1. Antes do código: SELECTs de diagnóstico/conversão e resultados em raw para
   revisão; sem gravar tabelas pelo chat.
2. Após aprovação: módulo com docstring da spec e os SELECTs revisados.
3. Testes em `test/` com dados sintéticos e DuckDB temporário real.
4. Evidência de tipos, valores, contagens, nulos, idempotência e falhas.
5. Suposições não previstas e critérios atendidos/pendentes.
