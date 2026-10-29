# Referências analisadas e adaptação

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

As quatro páginas foram efetivamente acessadas por `curl -L --fail` em
2026-10-28. O navegador de pesquisa retornou erro interno para as aulas; o
primeiro curl no sandbox falhou por DNS. A repetição com acesso autorizado
funcionou para todas. O HTML foi extraído com HTMLParser para leitura do conteúdo
principal, incluindo specs. Nenhum código do curso foi copiado.

| Referência | Método observado | Aplicação proposta neste projeto |
|---|---|---|
| [Aula 1](https://ckoliveiraa.github.io/pipeline-olist/aula-1.html) | uv bare, DuckDB local, raw fiel em texto, decisão → spec → código → conferência; ingestão idempotente | Configuração sem build-system; arquivos → quatro tabelas raw; verificar tudo antes de gravar; contar no destino |
| [Aula 2](https://ckoliveiraa.github.io/pipeline-olist/aula-2.html) | Investigar nulos, duplicatas, tipos e chaves antes de limpar; dinheiro DECIMAL, IDs texto, conversões explícitas, antes/depois | Datas reais são dia/mês/ano; encoding distinto por arquivo; nenhuma limpeza artificial; conflito de PK interrompe |
| [Aula 3](https://ckoliveiraa.github.io/pipeline-olist/aula-3.html) | Pergunta e grão antes do JOIN; CTE para ajustar grão; SQL numerado, executor sem regra; recriação transacional, vazio falha, reconciliação | Uma linha de item permanece uma linha após N:1; receita por quantidade × preço; receita por pedido antes do ticket; dez marts candidatos |
| [Aula 4 / desafio](https://ckoliveiraa.github.io/pipeline-olist/aula-4.html#desafio) | Rascunho antes do painel; apresentação só SELECT; leitura read_only fechada; testes sintéticos versus qualidade real; cobertura ≥60%; histórico incremental autoral | Dashboard só após validar marts, módulos painel/app separados; test/ e DuckDB temporário; publicação e commits após aprovação |

## Decisões que não são transferíveis da Olist

O grão da pizzaria não vira “um pedido” em todas as tabelas: item, variante e
tipo têm grãos próprios. Receita exige multiplicar quantidade por preço,
diferentemente do preço por item no exemplo Olist. Não existem status de pedido,
frete, clientes ou avaliações para reproduzir filtros ou indicadores da Olist.
Dinheiro será apresentado em USD conforme o dicionário, não em reais.
Deduplicação não será aplicada apenas por aparecer na aula: o dado observado
não tem duplicatas. A spec de transformação é proposta sujeita à revisão.

## Identificação dos conteúdos acessados

SHA-256 do HTML baixado (cópias de leitura em `/tmp/pizza-aula-N.html`):

| Aula | SHA-256 |
|---|---|
| 1 | `73ee3c5c78c593c8b54b219f5445c61bf924449f35e75dd271b364fc9e4c7560` |
| 2 | `2067e045f26af8279880ca5f678028dcd9ed067bd497bc6e4db315b63d98758b` |
| 3 | `0929342628562d2e6326983c459f385de5c3232a29990fea1832a34eef468921` |
| 4 | `8056ac74f3cd99b100cfde380db6e735ab113cb95ac45c4d37988c32001e7051` |

Os hashes identificam a consulta, não congelam a versão futura do site.

## Correção de aderência após revisão do usuário

A primeira versão dos documentos adotou seções genéricas e uma tabela de
contratos em indicadores.md. Isso não reproduzia o formato pedido pelas aulas.
Na revisão, os exemplos locais das aulas 1–3 foram relidos e a página
[Indicadores da turma](https://ckoliveiraa.github.io/pipeline-olist/indicadores.html),
vinculada pelas aulas, também foi acessada por curl para comparação.

Correções concretas:

- `indicadores.md`: dez linhas “indicador — tabelas (colunas) — o que mede”,
  oito cruzando tabelas; hipóteses pendentes marcadas com `?` e explicadas.
- Definições e contratos preservados em `docs/contratos-indicadores.md`.
- Specs de implementação: CONTEXTO, STACK, O QUE JÁ EXISTE, ARTEFATO A PRODUZIR,
  SPEC numerada, CRITÉRIOS DE ACEITE e ENTREGA, com motivos junto às regras.
- Ingestão segue as sete regras da aula 1; transformação segue as sete decisões
  da aula 2, com mapa completo de tipos; executor segue o contrato da aula 3.
- `specs/db.md` explicita a dependência de conexão antes da ingestão.

As diferenças próprias da pizzaria foram mantidas: encoding observado, datas
dia/mês/ano, quatro tabelas, IDs originais e receita estimada em USD. Nomes de
colunas e filtros da Olist não foram transferidos para este dado. As dependências
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
