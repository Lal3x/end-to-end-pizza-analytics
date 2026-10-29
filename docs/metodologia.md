# Método, decisões e participação da IA

Registro detalhado de desenvolvimento, mantido como consulta técnica. Para a
síntese atual das escolhas do autor e dos limites, leia [decisões](decisoes.md).

Correção de escopo solicitada pelo usuário: pipeline/ fica somente com as
etapas de ingestão, transformação com pandas e execução dos marts. Conexão
compartilhada em db.py na raiz, download em baixar_dados.py e SQL analítico
apenas para marts. A investigação de transformação por SQL documentada adiante
é histórica; seus executores e arquivos ativos foram removidos. O pedido do
usuário prevalece sobre qualquer interpretação anterior das referências.

Na correção efetivamente realizada, db.py foi movido para a raiz e a aquisição
foi concentrada em baixar_dados.py, eliminando o wrapper. O mapa de ingestão
fica na própria etapa; não há mais pipeline/aquisicao.py ou pipeline/fontes.py.
Os cinco SQLs de transformação, dois diagnósticos SQL, validador e nove testes
exclusivos dessa proposta foram retirados; permanecem no histórico Git e nos
relatórios anteriores. Não são convertidos em uma implementação fictícia de
pandas: naquele momento, pipeline/transformacao.py e pipeline/marts.py não existiam.

Verificações desta correção: .venv/bin/pytest --cov passou com 26 testes em
2,03 s; cobertura 98,08% de 156 linhas. Ruff check e format check aprovados,
assim como git diff --check. uv run python baixar_dados.py conferiu fontes já
existentes; a auditoria somente leitura produziu relatório idêntico ao anterior.
O SHA-256 de pizza.duckdb também permaneceu idêntico ao registrado antes da
correção. Nenhuma ingestão, transformação ou alteração de dados foi executada.
Formatação automática ajustou somente layout do mapa de ingestão; alterações
de código/configuração/documentação foram feitas por patches.

## Implementação da transformação com pandas

Após aprovação explícita do usuário, pipeline/transformacao.py implementa as
conversões em pandas, em um único módulo. Mantém nomes originais, IDs textuais,
dinheiro Decimal, precisão temporal e ocorrências de itens. As funções possuem
docstrings; as principais documentam parâmetros, retorno e falhas.

O primeiro ensaio integral falhou: DuckDB inferiu DECIMAL(4,2) por amostra de
objetos Decimal e encontrou um total maior adiante. A transação foi revertida.
A correção transporta dinheiro validado como texto exato e declara DECIMAL(18,2)
dentro da mesma transação. Um teste sintético com valor maior após a amostra
reproduz esse risco. Não há conversão monetária intermediária para float.

Auditorias SQL independentes conferem quatro FKs, COUNT de itens e soma exata
de preços por pedido antes do commit. Não são o mecanismo de transformação.
O ensaio completo passou em 25,205 s, pico RSS 1.616,36 MiB, com 54.041
repetições preservadas e zero divergências. As medições pertencem a esta
máquina; a ingestão e a transformação têm consumos diferentes.

Os relatórios JSON são saídas geradas pela execução, preservadas como evidência;
código e documentação foram editados por patches. Ruff format apenas ajustou
o layout dos arquivos Python novos.

## Implementação dos marts

Após revisão dos 13 contratos e autorização do usuário, pipeline/marts.py
executa um SELECT por arquivo em sql/marts. As auditorias ficam em dois SQLs
separados, preservando o executor sem fórmulas de negócio. Transação única,
fontes somente refined e docstrings nas funções seguem a spec.

Ensaio, reexecução e carga principal produziram 13 tabelas. Comparações por
EXCEPT ALL nos dois sentidos deram zero diferenças; RAW e refined permaneceram
iguais à cópia anterior. Registro, problemas reais da inspeção SQL/aliases e
limites de análise estão em docs/execucao-marts.md. Foram 86 testes, cobertura
92,42%; nenhum commit ou publicação externa realizado nesta etapa.

## Dashboard e registro dos commits acumulados

Em 29/10/2026 o usuário validou o desenho e autorizou o painel e a organização
dos commits pendentes. painel.py mantém leitura/formatos/figuras independentes
de Streamlit; app.py apenas apresenta e seleciona dados, com cache sem conexão.
112 testes passaram, cobertura 94,05%; a revisão visual incluiu desktop/móvel,
Pareto por nome, ranking SKU/Name, recarga e escrita dos marts com o servidor ativo.

O erro de automação ao clicar no input de radio estilizado foi corrigido usando
o rótulo visível, e a inspeção do Pareto levou a ticks explícitos de 0 a 100%
e identificação da linha de 80%. Resultados em docs/execucao-dashboard.md.
Código/docs foram alterados por patches; capturas e JSON são saídas geradas.

As alterações de estrutura, transformação, marts e desenho estavam acumuladas
sem commit. Foram registradas por conteúdo agora, com datas reais, junto à entrega
do dashboard. Isso não representa uma sequência de commits criada antes de cada
implementação; nenhum histórico foi reescrito ou retrodatado. AGENTS.md continua
ignorado e arquivos brutos/banco permanecem fora do Git. Não houve publicação externa.

Nota de versão: este registro descreve a fundação inicial Maven. A migração
autorizada para Pizza Paradise está em docs/migracao-pizza-paradise.md e nas
specs ativas. Na nova RAW, CSV fica texto e Parquet preserva tipos nativos;
order_items conserva repetições legítimas, diferentemente de deduplicação por PK.

## Método de desenvolvimento

Investigar os dados, escrever o contrato, implementar, executar e conferir os
resultados. Cada camada tem responsabilidade própria; grãos e relacionamentos
são definidos antes dos JOINs. Testes sintéticos verificam regras, enquanto
auditorias independentes reconciliam os resultados da fonte real.

Na fundação Maven, item, variante e tipo tinham grãos próprios; receita era
estimada por quantidade × preço de catálogo. Essas decisões são históricas.
Os contratos atuais de Pizza Paradise estão em docs/contratos-indicadores.md.

## Correção de aderência após revisão do usuário

A primeira versão dos documentos adotou seções genéricas e uma tabela de
contratos em indicadores.md. A revisão separou a lista resumida dos indicadores
dos contratos detalhados e padronizou as specs.

Correções concretas:

- `indicadores.md`: dez linhas “indicador — tabelas (colunas) — o que mede”,
  oito cruzando tabelas; hipóteses pendentes marcadas com `?` e explicadas.
- Definições e contratos preservados em `docs/contratos-indicadores.md`.
- Specs de implementação: CONTEXTO, STACK, O QUE JÁ EXISTE, ARTEFATO A PRODUZIR,
  SPEC numerada, CRITÉRIOS DE ACEITE e ENTREGA, com motivos junto às regras.
- Ingestão separa preservação e carga; transformação declara decisões e mapa
  completo de tipos; executor de marts mantém as fórmulas nos SQLs.
- `specs/db.md` explicita a dependência de conexão antes da ingestão.

As diferenças próprias da pizzaria foram mantidas: encoding observado, datas
dia/mês/ano, quatro tabelas, IDs originais e receita estimada em USD. As dependências
futuras são distinguidas dos artefatos que realmente existem na Etapa Zero.

## Execução completa — Pizza Paradise, 29/10/2026

Após spec e aprovação, executar_pipeline.py passou a controlar uma transação
para as três camadas. A pré-validação foi extraída na ingestão; as três etapas
aceitam conexão emprestada e preservam os comandos individuais. Não houve cópia
de regras de negócio no executor ou novo módulo na pasta pipeline/.

Quinze testes novos verificam falhas reais depois de ingestão e transformação,
rollback completo, destino novo/existente, schemas externos e interrupção.
Os 127 testes passaram, cobertura 94,81%. Ensaio/reexecução e carga principal
reconciliaram todas as 23 tabelas por valores, tipos e multiplicidades.

O comparador inicial encontrou falta do adaptador opcional pytz ao usar fetchall
em TIMESTAMPTZ; a comparação passou a usar JSON nativo e DESCRIBE, sem modificar
conversões de produção ou adicionar dependência apenas para o teste.
Medições, backup local e cuidados de operação: docs/execucao-pipeline.md.
Nenhum commit foi criado nesta etapa; mudanças preparadas para revisão.

## Automação e organização da entrega — 29/10/2026

CI, pre-commit, MkDocs e CD foram preparados após spec. Uma cópia sem dados nem
banco recebeu um ambiente novo: 127 testes passaram, cobertura 94,81%. Depois,
aquisição e pipeline reais reproduziram as 23 tabelas sem diferenças. O build
estrito passou e um .env artificial foi corretamente bloqueado pelo hook.
O formatador dos hooks ajustou somente a quebra final de dois JSONs históricos,
sem alterar seus valores. A documentação distingue fonte atual e histórico.

Foram criados commits locais das ferramentas e do executor que estava pendente,
sem retrodatação. Por escolha do usuário, envio e ativação do Pages ficam para
depois. Resultados e limites em [validação da automação](execucao-automacao.md).

## Revisão editorial da entrega — 29/10/2026

As referências didáticas foram retiradas do README, dos relatos e dos metadados
de consulta da evidência revisao-specs-sao-paulo.json, por solicitação do usuário.
Métricas, resultados das auditorias e decisões técnicas foram preservados.
O checklist passou a distinguir núcleo da entrega, complementos e publicação
pendente. Os registros antigos continuam identificados como históricos.
