# Validação dos SELECTs candidatos da refined

Status: investigação concluída; decisões propostas aguardam revisão antes de
implementar pipeline/transformacao.py. Nenhuma refined foi criada.

## Entradas e artefatos

Usada a RAW Pizza Paradise já auditada. Cinco SELECTs em sql/transformacao/,
dois diagnósticos monetários em sql/diagnostico/ e o script auxiliar
scripts/validar_selects_refined.py. A spec foi atualizada antes das consultas
com a regra monetária proposta e a execução exclusivamente em leitura.

O [relatório JSON](evidencias/validacao-selects-refined.json) é saída gerada,
não texto ajustado manualmente. Inclui diagnósticos SQL, resultados, hashes
dos SELECTs, nulos e tipos.

## Resultados realmente observados

| Tabela | Linhas RAW | Linhas do SELECT | Transformação proposta |
|---|---:|---:|---|
| orders | 2.046.713 | 2.046.713 | IDs texto; total DECIMAL; precisão temporal explícita |
| order_items | 2.916.015 | 2.916.015 | Todas as ocorrências preservadas |
| products | 36 | 36 | Price DECIMAL; Launch DATE com duas correções |
| customers | 34.761 | 34.761 | IDs preservados; coordenadas DOUBLE |
| stores | 32 | 32 | IDs/zipcode texto; coordenadas/distance DOUBLE |

43 diagnósticos, zero falhas: obrigatoriedade, conflitos de PK, domínios,
quatro FKs e reconciliação por pedido. Cada Name aponta para uma categoria.
Nenhuma alteração foi persistida: mudanças existem somente nos SELECTs.

### Decisão proposta 1 — precisão temporal

Preservar orderDate e acrescentar order_date DATE, order_timestamp TIMESTAMPTZ
opcional e timestamp_precision VARCHAR.

| Precisão | Registros | Resultado proposto |
|---|---:|---|
| Segundos e Z | 2.012.617 | Timestamp UTC com segundos |
| Minutos e Z | 33.980 | Timestamp UTC com segundos zero, precisão minute |
| Somente data | 116 | Data preservada; timestamp NULL; precisão date |

Nenhum nulo adicional nas colunas originais. Os 116 timestamps nulos são
intencionais, não erros de conversão. Não inventar meia-noite. O período usa a
data representada na origem; não se presume horário comercial local da loja.

### Decisão proposta 2 — correção restrita de Launch

PZ026 e PZ027: 2020-01-01, → 2020-01-01. Remover somente uma vírgula terminal
quando o restante casar com ISO exato; strptime valida o calendário. Formatos
ou sufixos diferentes falham, sem limpeza genérica.

### Decisão proposta 3 — normalização monetária

total DOUBLE: tolerância absoluta máxima 1e-9 unidade monetária entre original
e DECIMAL convertido de volta a DOUBLE. Maior desvio medido:
2.842170943040401e-14; zero valores fora da tolerância. Rejeitar negativos,
não finitos, fora da precisão ou com fração real além da regra.
Price textual: inteiro não negativo ou decimal com uma/duas casas; terceira
casa rejeitada, não arredondada. Dinheiro de saída: DECIMAL(18,2).

Depois da conversão, soma de Price das ocorrências coincide com total em cada
pedido e COUNT de ocorrências coincide com nItems: zero divergências. Todas
as 54.041 repetições legítimas de itens permanecem.

## Comandos, testes e problemas

- Consulta inicial somente leitura: precisão monetária, domínios e catálogo.
- .venv/bin/python scripts/validar_selects_refined.py redirecionado ao JSON:
  saída zero; catálogo e SHA-256 do banco antes/depois idênticos. Nenhuma tabela
  ou view, nem temporária, foi criada.
- uv run python scripts/validar_selects_refined.py: comando do README executado;
  cmp confirmou relatório idêntico ao da execução anterior.
- .venv/bin/pytest --cov: 35 testes passaram em 2,16 s, incluindo nove casos
  novos com fontes sintéticas e DuckDB temporário: formatos/calendário,
  precisão, nulo intencional, ocorrências, Launch restrito, IDs/coordenadas e
  diagnósticos monetários (inclusive NaN, infinito, fração real e overflow).
- Cobertura Python do pipeline existente: 98,71% de 155 linhas; não mede SQL
  ou o futuro módulo de transformação. O validador auxiliar segue fora da
  cobertura, conforme configuração existente.
- Ruff apontou variável de laço sem uso e linhas longas; corrigidas por patches.
  Ruff format ajustou layout de script/testes, exceção apenas para formatação.

## Aceite e próximo passo

Atendidos: SELECTs rastreáveis, contagens preservadas, conversões executadas,
falhas controladas em exemplos sintéticos, PK/FK, reconciliações, nulos
explicados e banco inalterado. Não houve suposição de negócio silenciosa.

Pendentes: revisão das três decisões propostas, implementação do executor
transacional e testes próprios de persistência, rollback e idempotência.
SELECT validado não comprova rollback de uma refined inexistente.
A moeda de apresentação também permanece pendente. Nenhum mart foi implementado.
