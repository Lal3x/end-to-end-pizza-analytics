# Registro da Etapa Zero — 28/10/2026

## Arquivos e decisões

Criados AGENTS.md, README.md, indicadores.md, .gitignore, .python-version,
specs/{etapa-zero,ingestao,transformacao,marts}.md,
docs/{fontes-e-licenca,metodologia,modelo,plano,execucao-etapa-zero}.md,
scripts/inspecionar.py e evidências JSON. Alterado pyproject.toml preexistente:
Python >=3.14.4 sem dependências → Python 3.13 e stack solicitada.

Gerados pelo uv: uv.lock e .venv. ZIP em data/, cinco CSVs originais em raw/;
esses diretórios estão no .gitignore. JSON de inventário é saída gerada do
script, e JSON de licença é resposta copiada da API pública. Extração/cópia,
lockfile e formatação Ruff usaram ferramentas próprias, em vez de apply_patch,
pois preservam bytes ou geram artefatos mecanicamente. Código e documentos
foram escritos por patches revisáveis.

## Comandos realmente executados e resultados

| Comando / operação | Resultado observado |
|---|---|
| Leitura do anexo; `pwd`, `ls -la`, `rg --files`, `cat pyproject.toml` | Projeto só tinha pyproject.toml visível com Python >=3.14.4; pasta correta |
| `uv --version`, `python3 --version` | uv 0.12.24; Python do sistema 3.14.4 |
| Abertura web das quatro aulas | Erro interno; sem conteúdo útil |
| `curl -L --fail --max-time 30` de cada aula para `/tmp/pizza-aula-N.html` | Primeiro acesso falhou por DNS; após autorização, quatro downloads bem-sucedidos |
| Extração de texto dos HTMLs com HTMLParser | Leitura dos fundamentos, specs e desafio; síntese e hashes em metodologia.md |
| Consulta web ao Kaggle, Maven e CC0 | Kaggle sem corpo textual; Maven com descrição/licença e metadados inconsistentes; termos CC0 acessíveis |
| `curl -L --fail --max-time 30 'https://www.kaggle.com/api/v1/datasets/list?search=maven-pizza-challenge-dataset' -o /tmp/pizza-kaggle-meta.json` | Referência exata com CC0: Public Domain; cópia em evidencias/kaggle-list.json |
| `curl -L --fail --max-time 60 'https://www.kaggle.com/api/v1/datasets/download/neethimohan/maven-pizza-challenge-dataset?datasetVersionNumber=1' -o /tmp/pizza-kaggle-v1.zip` | ZIP público obtido, sem login; copiado para data/pizza-kaggle-v1.zip |
| Inspeção preliminar via Python: ZipFile, csv.DictReader, Decimal e datetime | Colunas/contagens reais; UTF-8 inválido em pizza_types; dicionário declara USD |
| `python3 scripts/inspecionar.py data/pizza-kaggle-v1.zip > docs/evidencias/inspecao.json` | Inventário de todas as linhas, hashes, domínios e relações |
| `python3 -m zipfile -e data/pizza-kaggle-v1.zip raw` | Cinco membros extraídos, hashes depois conferidos |
| `uv python list --only-installed` | Primeiro falhou ao criar lock no cache read-only; com autorização listou 3.14.4 e avisou sobre shims pyenv |
| `uv sync --python /home/lucas/.pyenv/versions/3.13.14/bin/python3.13` | Python 3.13.14 utilizado diretamente; 46 pacotes resolvidos, 44 instalados; .venv e uv.lock gerados |
| `uv sync --locked` | Resolução/checagem bem-sucedida com lockfile |
| Importações e versões via `.venv/bin/python` | Todas as bibliotecas importadas; versões no README |
| `.venv/bin/ruff check .` | Primeira execução: três E501; após correção: All checks passed |
| `.venv/bin/ruff format scripts/inspecionar.py` e `ruff format --check .` | Script formatado; verificação final aprovada |
| `.venv/bin/python scripts/inspecionar.py ... > /tmp/pizza-inspecao-repetida.json`, `cmp ...` | JSON reproduzido byte a byte, saída zero |
| Verificação hashlib dos cinco CSVs e asserts de ausência de banco/pipeline | Todos os hashes iguais ao ZIP; nenhum pizza.duckdb ou pipeline/ criado |
| `git status --short` | Fatal: not a git repository; .git não funcional; sem tentativa de alterar diretório protegido |

Validação final dos comandos do README, executada com saída zero:

- `uv run python --version`: Python 3.13.14.
- `uv run python -c "import duckdb, pandas, streamlit, plotly, pytest, pytest_cov"`:
  importações sem erro.
- `uv run python scripts/inspecionar.py data/pizza-kaggle-v1.zip`: mesmo inventário.
- `uv run python -m zipfile -e data/pizza-kaggle-v1.zip raw`: extração sem erro.
- `uv run ruff check .`: All checks passed!
- `uv run ruff format --check .`: todos os arquivos aprovados.
- Download repetido diretamente para `data/pizza-kaggle-v1.zip` com o mesmo
  comando curl do README: sucesso; mesmo SHA-256 posteriormente conferido.

A criação de diretórios e as cópias foram feitas com mkdir/cp; não alteraram
conteúdo das fontes. O comando pytest é explicitamente futuro no README e
não foi executado; os módulos e testes ainda não existem.

## Resultados, testes e limites

Contagens: 21.350 pedidos, 48.620 linhas de itens, 96 variantes, 32 tipos e 15
linhas no dicionário. Zero campos vazios/duplicatas de PK/linhas exatas nas
fontes de negócio; zero órfãos nas três FKs; cinco variantes sem venda.
Formatos reais de data/hora e domínios estão no inventário, não inferidos de
amostras. Nenhuma ingestão ou reconciliação financeira de marts foi executada.

Não há teste unitário de pipeline nem cobertura nesta etapa, pois os módulos
estão deliberadamente ausentes. Verificações executadas: importação, resolução
do ambiente, Ruff, repetição de inventário, integridade dos arquivos e escopo.
Elas não equivalem à suíte pytest e aos testes de dados das próximas etapas.

## Critérios atendidos e pendentes

Atendidos: quatro referências acessadas; licença da republicação evidenciada;
quatro fontes inspecionadas; modelo/grãos/PK/FK e perguntas definidos em proposta;
ambiente 3.13 instalado/importável; docs e specs anteriores ao pipeline; escopo
respeitado. Pendentes: revisão do usuário, aprovação das decisões propostas,
repositório Git gravável e autorização para primeiro commit. Critérios finais
do projeto (camadas, SQLs, reconciliações, suíte, cobertura e dashboard) continuam
pendentes e não são requisito para alegar execução nesta etapa.

## Suposições e problemas

cp1252 é escolha compatível, não encoding comprovado pelo exportador. Modelo,
grão do ranking, política de duplicatas/nulos e preço de catálogo são propostas,
não decisões aprovadas. Não se acrescentou fuso, status ou entidade cliente.
Não houve hipótese adicional não registrada no contrato ou propostas.

Problemas observados e resolvidos: acesso web/DNS, cache uv read-only, shims
pyenv indisponíveis e três violações Ruff. Pendência não resolvida: Git não
funcional neste workspace. Nenhum commit, remoto ou publicação foi criado.

Próximo passo: revisão da Etapa Zero e commit de fundação autorizado, seguido
pela spec de conexão e pela ingestão. A exigência de revisão vem diretamente
da seção “PRIMEIRA TAREFA — ETAPA ZERO” do pedido do usuário.

## Revisão solicitada: formato das aulas

O usuário apontou que specs e indicadores não seguiam o padrão das aulas.
A comparação confirmou: faltava a estrutura de contrato/prompt nas specs e a
lista de uma linha por indicador pedida no desafio 1.

Arquivos alterados: indicadores.md, specs/ingestao.md, specs/transformacao.md,
specs/marts.md, README.md, docs/metodologia.md e este registro. Criados
specs/db.md e docs/contratos-indicadores.md; este último preserva o conteúdo
analítico antes concentrado em indicadores.md.

Comandos realmente executados nesta revisão:

- Leitura dos documentos por cat/rg e releitura dos exemplos dos HTMLs locais
  das aulas usando HTMLParser.
- `curl -L --fail --max-time 30 https://ckoliveiraa.github.io/pipeline-olist/indicadores.html -o /tmp/pizza-aula-indicadores.html`:
  página vinculada pelas aulas acessada com sucesso; texto lido com HTMLParser.
- Verificação por Python de dez linhas no formato com dois separadores `—`,
  oito com múltiplas tabelas, sete seções obrigatórias nas quatro specs de
  implementação, links locais e ausência de pipeline/banco: todos os asserts passaram.

Não houve alteração de código ou dados; pytest/cobertura não foram executados.
A revisão documental não equivale à aprovação das decisões de negócio.
Pendências e próximo passo permanecem: revisão da Etapa Zero antes de implementar.

## Atualizações posteriores da revisão

- Indicadores receberam nomes e descrições orientados ao negócio, preservando
  as dez entradas e a rastreabilidade de tabelas/colunas.
- O candidato de concentração foi detalhado como Pareto da receita por tipo:
  grupo que alcança pelo menos 80%, incluindo o tipo que cruza o limite, sem
  presumir relação 80/20. A solicitação de inclusão não aprovou o contrato final.
- O usuário aprovou uso do preço de catálogo para estimar receita em USD,
  nomes originais e IDs texto, remoção somente de duplicatas exatas na refined
  e falha em conflitos de chave ou conversões inválidas. RAW permanece fiel.
- O usuário reservou expressamente a validação dos indicadores para discussão
  conjunta. A Etapa Zero ainda não foi aprovada integralmente.
- Plano corrigido para reconhecer specs/db.md existente; contrato esclarece
  receita por pedido no mart 05 e ticket global no mart 10, ambos lendo refined.

Alterações restritas à documentação; nenhum módulo de pipeline, commit ou
resultado de cálculo foi produzido por essas aprovações parciais.

## Validação dos indicadores e separação dos rankings

O usuário escolheu ranking por variante, separando tipo e tamanho, e solicitou
outro indicador consolidado. O candidato 02 passou a ter grão pizza_id; foi
acrescentado 11_ranking_tipos_pizza com grão pizza_type_id, preservando os
demais números de arquivos propostos. Agora há onze candidatos, incluindo o
resumo executivo, que é uma consolidação de medidas e não uma medida nova.

O parecer de cada candidato foi registrado em indicadores.md. Todos têm fontes
e relações suficientes sob a hipótese de receita já aprovada; a validade dos
resultados futuros ainda exige testes e reconciliações. O Pareto continua por
tipo como proposta, não foi convertido automaticamente para variante.

Verificação realmente executada: Python com csv.DictReader sobre as quatro
fontes locais, encodings declarados, unicidade das chaves, associação das FKs e
conjuntos de variantes/tipos vendidos. Resultado: 48.620 itens, 91 variantes com
vendas, 32 tipos com vendas, 29 tipos com múltiplos tamanhos vendidos, zero
pedidos sem itens e relações válidas. Nenhum mart ou receita agregada foi
calculado nessa conferência. Alterações restritas à documentação; sem pipeline,
commit ou aprovação presumida do conjunto completo de indicadores.

## Autorização para o próximo passo

Após o parecer sobre os onze candidatos, o usuário autorizou avançar. A seleção
e as definições estão validadas para desenvolvimento incremental. A aprovação
não constitui resultado de execução ou autorização específica para commits.

Na preparação do próximo passo foram lidos specs/db.md, pyproject.toml e
AGENTS.md; `git status --short` foi repetido e ainda retornou `fatal: not a git
repository`. O diretório .git está somente leitura no workspace. Para cumprir
o histórico por etapas, é necessário disponibilizar um repositório gravável e
autorizar o commit de fundação antes de iniciar os módulos de conexão/ingestão.

## Retomada com Git disponível

Após configurar o Git e solicitar continuação, o usuário deixou o repositório
na branch dev. `git status --short --branch`, `git log -3 --oneline` e
`git show --stat --oneline HEAD` confirmaram o commit beab954 (first commit),
contendo somente README.md. Specs, configurações e outros documentos ainda
estavam não rastreados. A indisponibilidade anterior do Git foi resolvida;
preparar o registro desses artefatos antes de implementar db.py.
