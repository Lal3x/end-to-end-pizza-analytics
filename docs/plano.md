# Etapas e pontos de revisão

Cada etapa segue investigação → spec → aceite → implementação → execução →
evidências → preparação de commit. Commits exigem autorização e devem ocorrer
na etapa real, antes de iniciar a seguinte; não haverá reconstrução posterior.

| Etapa | Entrega | Porta de validação |
|---|---|---|
| Zero — atual | Fonte/licença, inventário, modelo, indicadores, specs iniciais, ambiente | Revisão do usuário antes de qualquer pipeline; preparar commit de fundação |
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

## Pendências para a revisão atual

- Aprovar fonte Kaggle v1 e manter dados fora do Git.
- Seleção dos onze candidatos validada para avançar; ajustes posteriores devem
  ser registrados antes da implementação do indicador afetado.
- Revisar política proposta de nulos e novos
  domínios; não houve necessidade de limpeza no dado atual.
- Revisar os tipos propostos DATE e TIME, sem fuso informado.
- Registrar as specs, configurações e documentos no Git antes do código.
  O repositório agora funciona na branch dev e tem o commit beab954 com README;
  os demais artefatos de fundação ainda precisam ser versionados.

## Próximo passo

Revisar a Etapa Zero, resolver as decisões acima e preparar o commit de
fundação. A spec de conexão já existe em specs/db.md; após a revisão completa,
validá-la e implementar/testar o módulo de conexão antes da ingestão.
