# Etapas e pontos de revisão

Cada etapa segue investigação → spec → aceite → implementação → execução →
evidências → preparação de commit. Commits exigem autorização e devem ocorrer
na etapa real, antes de iniciar a seguinte; não haverá reconstrução posterior.

| Etapa | Entrega | Porta de validação |
|---|---|---|
| Zero — concluída | Fonte/licença, inventário, modelo, indicadores, specs iniciais, ambiente | Revisada pelo usuário; fundação registrada em fd85358 |
| 1 — ingestão | Spec de conexão/caminhos e ingestão revisadas; db.py e ingestao.py | Fontes pré-validadas, valores VARCHAR/nulos preservados, idempotência, testes sintéticos e contagens reais |
| 2 — transformação | Reinvestigação de raw, SELECTs de conversão para revisão, spec final, transformacao.py | Tipos, antes/depois, PK/FK, nenhum erro silencioso; executar só decisões aprovadas |
| 3 — marts | Fechar definições; onze SQLs e executor transacional | Grãos/JOINS conferidos, financeiros reconciliados, rollback e testes sintéticos |
| 4 — visualização | Spec visual, design/rascunho.png antes do código; painel.py/app.py; HTML se viável | Somente marts/read_only, conexão fechada, unidades USD, filtros com escopo claro; conferir no navegador |
| 5 — validação consolidada | Ampliar testes já criados nas etapas; qualidade independente | pytest-cov ≥60% real, Ruff, dados temporários, falhas/rollback e formatação |
| 6 — documentação e entrega | README final, registro IA e decisões, licença de código a escolher | Executar todos os comandos do README final; revisão do histórico; publicar apenas com autorização |

## Decisões aprovadas pelo usuário

- Usar o preço de catálogo para estimar receita em USD, mantendo explícita a
  limitação de não existir preço transacional histórico.
- Manter os nomes originais; identificadores permanecem como texto (VARCHAR).
  Quantidades, preços, datas e horas seguem os tipos próprios da transformação.
- Na refined, remover somente duplicatas exatas, com contagem explícita;
  interromper em conflitos de chave e conversões inválidas. RAW preserva tudo.
- Ranking principal por variante (tipo e tamanho separados); acrescentar um
  ranking consolidado por tipo, somando seus tamanhos.

Após a validação conjunta dos indicadores, o usuário autorizou seguir para o
próximo passo. A seleção dos onze candidatos, incluindo os rankings separados
e consolidado e o Pareto por tipo, está aprovada para implementação incremental.
Permanece a necessidade de preparar o versionamento antes de começar o código,
para preservar o histórico real por etapa. Commits e publicação ainda dependem
de autorização específica.

## Estado atual e pendências

- Aprovar fonte Kaggle v1 e manter dados fora do Git.
- Seleção dos onze candidatos validada para avançar; ajustes posteriores devem
  ser registrados antes da implementação do indicador afetado.
- Revisar política proposta de nulos e novos
  domínios; não houve necessidade de limpeza no dado atual.
- Revisar os tipos propostos DATE e TIME, sem fuso informado.
- Fundação registrada em fd85358, na branch dev, após beab954 (README).
- Módulo db.py implementado: sete testes passaram, com cobertura de 100% das
  suas 20 linhas executáveis. Evidências em docs/execucao-db.md.

## Próximo passo

Registrar o incremento de conexão e seus testes; em seguida implementar a
ingestão conforme specs/ingestao.md, com testes sintéticos e conferência real.
