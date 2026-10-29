# Plano de migração e desenvolvimento — Pizza Paradise

O usuário autorizou substituir a fonte atual por Pizza Paradise.
Trabalhar por etapas, com specs anteriores ao código, validação e commits reais.
Sem reescrever histórico ou publicar fontes completas sem licença esclarecida.

| Etapa | Entrega | Aceite |
|---|---|---|
| Migração da fundação | Modelo, fonte, indicadores e specs atualizados | Preservar histórico Maven; registrar diferenças de grão e formatos |
| Aquisição/ingestão | Cinco fontes, CSV via pandas e Parquet via DuckDB | Hashes, tipos, contagens, valores, multiplicidades, rollback e idempotência |
| Transformação | Revisar contrato e implementar em pandas no módulo da etapa | Datas/precisão, Launch, dinheiro, quatro PKs e quatro FKs; preservar itens repetidos |
| Marts | Um SQL numerado por pergunta | Sem média de médias; reconciliação entre pedido e itens; grãos declarados |
| Dashboard | Rascunho antes do visual, painel/app separados | Somente marts, read_only e conexão fechada |
| Entrega | README executável, testes e cobertura ≥60% | Resultados reais, licença/atribuição e histórico incremental |

## Decisões já autorizadas

- Migrar para Pizza Paradise sem trocar Python, uv, DuckDB, pandas, SQL e testes.
- Preservar nomes originais, IDs como texto na refined.
- Comparar variantes separadas e produtos consolidados; Pareto e resumos.
- Preservar a fonte anterior e registrar a migração, sem inventar histórico.
- Manter AGENTS.md apenas local, ignorado pelo Git.
- Transformação em pandas, em um único módulo, com docstrings nas funções.
- Adicionar precisão temporal, manter horários Z em UTC, corrigir os dois
  valores Launch conhecidos e aceitar apenas ruído monetário até 1e-9.

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

Aquisição/ingestão e transformação pandas concluídas. Cinco tabelas refined
publicadas; zero órfãos ou diferenças por pedido. Reexecução de ensaio e carga
principal conferidas. Registro em docs/execucao-transformacao.md. Na conclusão
da transformação eram 61 testes, cobertura 94,12%; Ruff aprovado.
Pico RSS da transformação principal:
1.575,04 MiB nesta máquina, diferente do consumo da ingestão.

Marts implementados após revisão dos 13 contratos: arquivos numerados,
pipeline/marts.py e duas auditorias SQL independentes. Treze tabelas publicadas;
86 testes passaram, cobertura total 92,42%, Ruff aprovado. Registro em
docs/execucao-marts.md.

Rascunho HTML concluído em 29/10/2026 com números dos marts e capturas PNG
desktop/móvel. Spec em specs/dashboard.md; auditoria em docs/execucao-rascunho.md.
Período completo, sem filtro global; alternância mensal altera apenas a série.
Desenho validado; painel.py/app.py implementados em 29/10/2026, com tema ciano,
recarga e sete figuras Plotly. 112 testes passaram, cobertura 94,05%; navegador
desktop/móvel verificado e marts reexecutados sem lock com Streamlit aberto.
Registro em docs/execucao-dashboard.md. Próximo passo: revisão final da entrega,
comandos do README e pendências de fonte/publicação; relatório HTML é opcional.
Revisão de 29/10/2026: specs padronizadas, Pareto com nomes e mart horário em
America/Sao_Paulo; 87 testes aprovados. Registro em docs/validacao-specs-e-fuso.md.

Execução completa implementada em 29/10/2026 em executar_pipeline.py, na raiz,
reutilizando as três etapas com uma transação de destino. Ensaio, reexecução e
principal publicados; comparação integral das 23 tabelas sem diferenças.
127 testes aprovados, cobertura 94,81%; registro em docs/execucao-pipeline.md.
Comandos individuais preservados. Nenhum commit novo nesta etapa.

Revisão final local: CI, pre-commit, MkDocs e CD preparados. Ambiente novo com
127 testes aprovados e 94,81% de cobertura; nova aquisição e execução reproduziram
as 23 tabelas. Ferramentas e executor registrados em commits locais. A publicação
foi adiada por escolha do usuário; próximo passo é seguir docs/automacao.md para
enviar dev, revisar a PR e ativar Pages. Evidências em docs/execucao-automacao.md.
