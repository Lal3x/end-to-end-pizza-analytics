# CI, pre-commit, documentação e entrega

Status: autorizado em 29/10/2026. Contrato anterior à configuração das ferramentas.

## CONTEXTO

Concluir a revisão de entrega e automatizar qualidade/documentação do projeto
autoral. Repositório Lal3x/end-to-end-pizza-analytics, público, padrão main;
desenvolvimento atual em dev. Não reescrever histórico nem publicar dados brutos.

## STACK

Python 3.13, uv com uv.lock, pytest/cov e Ruff existentes; pre-commit para hooks,
MkDocs para documentação estática e GitHub Actions/Pages para CI/CD.
Sem alteração dos indicadores, banco, dashboard ou infraestrutura do pipeline.

## O QUE JÁ EXISTE

Pipeline completo e dashboard validados, 127 testes, fontes e banco locais
ignorados. Executor completo ainda sem commit. Documentos de operação, specs,
históricos e evidências reais existentes. A fonte tem permissão textual ampla,
sem licença padronizada nos metadados; não atribuir CC0/ISC aos cinco anexos.

## ARTEFATOS A PRODUZIR

.github/workflows/ci.yml, .pre-commit-config.yaml, mkdocs.yml, guias de entrada,
automação e entrega em docs/, ajustes do README e dependências dev/docs no lock.
Hook de MkDocs para apontar links de código/design/specs ao GitHub, sem copiar
árvore inteira do projeto para o site. Registro final dos checks e do deploy.

## SPEC

### 1. CI

Executar em push, pull_request e acionamento manual, Python 3.13 e uv fixado.
uv sync --locked --group docs; pre-commit em todos os arquivos; pytest --cov;
mkdocs build --strict. Testes só com fontes sintéticas, sem rede ou banco real
como dependência. Não executar downloader/pipeline real no CI.
Permissão contents: read; passos externos fixados por SHA verificado.
Motivo: repetir os mesmos controles em ambiente limpo, sem segredos de produção.

### 2. PRE-COMMIT

Hooks locais chamam uv run --locked para compartilhar versões do lock: Ruff,
formato, YAML/TOML, conflitos, espaços/fim de arquivo, arquivos grandes e chaves
privadas. Nenhum hook usa banco real.
Bloquear também caminhos de fontes/bancos/caches/.env/AGENTS.md, inclusive se
adicionados à força. O controle lê apenas nomes dos arquivos.
Instalar no clone atual e documentar uv run pre-commit install; clones novos
precisam instalar seus próprios hooks.
Motivo: impedir divergência entre checks locais e CI.

### 3. MKDOCS E ORGANIZAÇÃO

README curto como entrada; site com início, execução do zero, dados/modelo,
indicadores, operação, desenvolvimento, critérios de entrega e histórico.
Preservar relatórios antigos com data/contexto; não tratar Maven como fonte ativa.
Build estrito; links de arquivos externos a docs/ apontam ao código no GitHub.
Tema claro com identidade ciano e navegação em português; site gerado ignorado.
Motivo: documentação navegável sem duplicar regras ou apagar evidências.

### 4. CD E PUBLICAÇÃO

Após CI aprovado na main, gerar artefato apenas de site/ e publicar com ações
oficiais do GitHub Pages, ambiente github-pages e OIDC. Deploy depende do job
de qualidade, com permissions pages: write e id-token: write somente nesse job.
Nunca usar pull_request_target, token pessoal no workflow ou upload da raiz.
No dev/PR, somente validar; sem deploy de conteúdo de PR.
Motivo: manter o site publicado correspondente a uma revisão aprovada no CI.

Pages é documentação estática; não hospeda servidor Streamlit. Se Pages ainda
não estiver habilitado, configurar fonte GitHub Actions quando houver acesso.
Se faltar autenticação/permissão, concluir configuração e build local e registrar
o bloqueio exato; não afirmar que o site/CI remoto rodou sem confirmação.

### 5. REVISÃO DA ENTREGA E FONTE

Validar ambiente uv novo, testes sem banco/fontes reais e, separadamente,
aquisição/pipeline em destino isolado. Não sobrescrever o banco do usuário.
Revisar termos do publicador e atribuição; publicar código, guias e resultados
derivados/evidências pequenas. Excluir CSV/Parquet originais, banco, backups,
credenciais, caches e AGENTS.md; não inventar licença padronizada dos anexos.
Guardar distinção entre permissão textual e metadados license:null.

### 6. GIT E FALHAS

Registrar executor completo e automação em commits reais e separados. Revisar
diff, arquivos versionados e resultado dos checks antes de enviar ao GitHub.
Não fazer force-push nem reconstruir cronologia. Manter branch dev e integração
normal na main para o deploy; respeitar proteções remotas e relatar impedimentos.
Falha de lint/teste/docs impede deploy. Logs não exibem tokens ou credenciais.

## CRITÉRIOS DE ACEITE

- Ambiente novo instala com --locked; hooks, testes/cobertura ≥60% e build
  estrito passam sem dados/banco do projeto na suíte.
- Navegação e links do MkDocs funcionam; site/ não inclui fontes brutas/banco.
- Fonte/atribuição/limites e método de reprodução explícitos na documentação.
- CI em PR/push; Pages só na main após qualidade; permissões mínimas.
- Instalação local do hook comprovada; commits refletem alterações reais.
- Remoto e URL pública conferidos quando acessíveis; pendências reais declaradas.

## ENTREGA

Configurações, lockfile atualizado, documentação, resultados locais/remotos e
limitações verificadas. Não iniciar serviços nem publicar dados completos para
aparentar conclusão. Registrar apenas ações e execuções realmente realizadas.
