# Execução da transformação — Pizza Paradise

Data: 28/10/2026. Contrato: [spec](../specs/transformacao.md).
Implementação: [pipeline/transformacao.py](../pipeline/transformacao.py).

O usuário aprovou explicitamente as colunas temporais, a correção restrita de
Launch e a tolerância monetária de 1e-9 antes do código. Transformações usam
pandas em um único módulo; SQL lê, persiste tipos físicos e audita o destino.
Nenhum executor SQL de transformação foi reintroduzido.

## Execução e resultado

Executado primeiro em cópia local de pizza.duckdb em /tmp; depois reexecutado
nesse banco e publicado no banco principal pelo comando:

```bash
uv run python -m pipeline.transformacao
```

Nesta sessão, o comando foi executado com .venv/bin/python, usando o ambiente
já instalado. Não foi necessário baixar dependências ou modificar o lockfile.
A saída JSON final está em [evidência](evidencias/transformacao-pandas.json).

| Tabela | Linhas RAW | Linhas refined | Duplicatas removidas |
|---|---:|---:|---:|
| orders | 2.046.713 | 2.046.713 | 0 |
| order_items | 2.916.015 | 2.916.015 | 0 |
| customers | 34.761 | 34.761 | 0 |
| stores | 32 | 32 | 0 |
| products | 36 | 36 | 0 |

54.041 ocorrências repetidas de itens foram preservadas. Os quatro pais têm
chaves únicas; as quatro FKs não têm órfãos. Em todos os pedidos, quantidade
confere com nItems e soma exata dos preços confere com total.

Precisão temporal: 2.012.617 segundos, 33.980 minutos, 116 somente data.
Os 116 têm order_timestamp nulo; nenhum horário foi inventado. UTC permanece
nos horários com Z. orderDate original foi preservado. PZ026 e PZ027 tiveram
somente a vírgula de 2020-01-01, removida de Launch; a saída é DATE.
IDs são VARCHAR; total e Price são DECIMAL(18,2). Ingredients pode continuar
nulo; não houve preenchimento artificial.

O banco principal e o ensaio reexecutado foram comparados nos dois sentidos
com EXCEPT ALL em todas as refined, incluindo multiplicidades. Zero diferenças.
A auditoria RAW por valores, tipos, multiplicidades e hashes das fontes
produziu relatório idêntico ao de antes da transformação.

Ensaio inicial bem-sucedido: 25,205 s, pico RSS 1.616,36 MiB. Carga principal:
35,916 s, pico RSS 1.575,04 MiB. A carga principal e a reexecução do ensaio
ocorreram em processos concorrentes, portanto esses tempos não são um benchmark
isolado. Pico RSS é do processo inteiro no Linux; não representa apenas pandas
nem garante desempenho em outra máquina.

## Problema encontrado e correção

O primeiro ensaio integral falhou ao persistir objetos Decimal: a inferência
por amostra do DuckDB escolheu DECIMAL(4,2), insuficiente para um total posterior
de 108.95. A transação foi revertida. O banco principal não foi afetado.

A correção transporta os Decimal já validados como strings exatas, e declara
DECIMAL(18,2) dentro da transação, antes das auditorias e do commit. Não existe
arredondamento financeiro em SQL ou conversão monetária intermediária em float.
Um teste com total maior após as primeiras 1.000 linhas cobre essa regressão.

## Verificação e continuidade

61 testes sintéticos passaram em 4,76 s; cobertura 94,12% de 323 linhas
executáveis. Cobrem formatos de datas, valores inválidos, dinheiro, conflitos,
domínios, repetições, reexecução e rollback de refined anterior em falhas de
conversão, FK, quantidade e receita. Ruff check e format check aprovados.

As funções da transformação têm docstrings. As funções principais de ingestão,
conexão e download também receberam documentação de parâmetros, retorno e erros.
Alterações de código/documentação foram feitas por patches; Ruff format ajustou
o layout e o JSON de evidência foi gerado a partir das execuções reais.

Na data desta execução, marts e dashboard estavam pendentes; foram concluídos
posteriormente, conforme [marts](execucao-marts.md) e [dashboard](execucao-dashboard.md).
Moeda USD ainda depende da documentação
da fonte; não houve inferência de fuso comercial nem liberação de redistribuição
dos anexos. Nenhum commit ou publicação foi realizado nesta etapa.
