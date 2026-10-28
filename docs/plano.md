# Plano de migração e desenvolvimento — Pizza Paradise

O usuário autorizou substituir a fonte atual por Pizza Paradise.
Trabalhar por etapas, com specs anteriores ao código, validação e commits reais.
Sem reescrever histórico ou publicar fontes completas sem licença esclarecida.

| Etapa | Entrega | Aceite |
|---|---|---|
| Migração da fundação | Modelo, fonte, indicadores e specs atualizados | Preservar histórico Maven; registrar diferenças de grão e formatos |
| Aquisição/ingestão | Cinco fontes, CSV via pandas e Parquet via DuckDB | Hashes, tipos, contagens, valores, multiplicidades, rollback e idempotência |
| Transformação | Investigar nova RAW e revisar SELECTs antes do código | Datas/precisão, Launch, dinheiro, quatro PKs e quatro FKs; preservar itens repetidos |
| Marts | Um SQL numerado por pergunta | Sem média de médias; reconciliação entre pedido e itens; grãos declarados |
| Dashboard | Rascunho antes do visual, painel/app separados | Somente marts, read_only e conexão fechada |
| Entrega | README executável, testes e cobertura ≥60% | Resultados reais, licença/atribuição e histórico incremental |

## Decisões já autorizadas

- Migrar para Pizza Paradise sem trocar Python, uv, DuckDB, pandas, SQL e testes.
- Preservar nomes originais, IDs como texto na refined.
- Comparar variantes separadas e produtos consolidados; Pareto e resumos.
- Preservar a fonte anterior e registrar a migração, sem inventar histórico.
- Manter AGENTS.md apenas local, ignorado pelo Git.

## Diferenças que exigem contrato explícito

- Parquet mantém tipos nativos na RAW; CSV entra como texto.
- order_items preserva repetições, pois cada linha representa uma unidade.
- Não existe pizza_type_id; consolidação por Name exige checagem de consistência.
- orders.total precisa reconciliar com itens; não somar total após JOIN 1:N.
- 116 pedidos sem horário exigem classificação de precisão, sem hora inventada.
- Moeda: proposta de apresentação USD por contexto americano, ainda sem declaração
  explícita identificada nos anexos; não tratar isso como fato comprovado.
- Licença: permissão textual ampla do publicador, sem licença padronizada nos
  metadados dos cinco anexos. Código pode ser desenvolvido com arquivos locais;
  redistribuição dos anexos completos permanece pendente de esclarecimento.

## Próximo passo

Aquisição/ingestão validadas em banco separado, repetidas e publicadas em
pizza.duckdb após cópia íntegra do banco Maven. Suíte: 26 testes, cobertura
98,71%; pico RSS do ensaio aproximadamente 575 MiB. Registro e evidências em
docs/migracao-pizza-paradise.md. Próximo passo: investigar a nova RAW e validar
SELECTs temporais/monetários e correção Launch antes do código da refined.
