# CI, pre-commit e GitHub Pages

## Instalação local

```bash
uv sync --locked --group docs
uv run pre-commit install
uv run pre-commit run --all-files
```

O hook precisa ser instalado em cada clone; não é versionado dentro de .git/.
Hooks locais usam uv.lock: Ruff, formatação, YAML/TOML, conflitos, espaços/fim
de arquivo, arquivos grandes e chaves privadas. Ajustes de whitespace podem
modificar arquivos; revise o diff e adicione novamente ao staging.
Há também um bloqueio de caminhos locais (raw/, data/, bancos, .env e AGENTS.md),
mesmo se um arquivo for incluído à força contrariando o .gitignore.

## Documentação local

```bash
uv run mkdocs serve
uv run mkdocs build --strict
```

O servidor informa a URL local. site/ contém a saída estática e fica ignorado.
O MkDocs publica somente docs/; links de código/specs/design fora dessa pasta
apontam ao GitHub, sem copiar banco, fontes ou a árvore inteira para o artefato.
Registros históricos são excluídos pelo exclude_docs do mkdocs.yml, inclusive
da busca. Links para esses arquivos levam à versão preservada no repositório.

## CI

Pushes e pull requests executam instalação bloqueada pelo lock, pre-commit,
testes com cobertura e build estrito. A suíte usa DuckDB temporário e fontes
sintéticas; não baixa datasets nem executa cargas reais no runner.

## CD

Depois dos checks aprovados na main, o workflow publica o artefato site/ usando
as ações oficiais do Pages e OIDC, no ambiente github-pages. Branch dev e PRs
validam sem fazer deploy. Não há token pessoal guardado no workflow.

No GitHub: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
Se houver proteção de ambiente, permitir publicação pela main. URL prevista:
https://lal3x.github.io/end-to-end-pizza-analytics/.

Pages hospeda este site estático de documentação. Para o painel Streamlit,
execute app.py ou configure um serviço próprio de aplicação em outra entrega.

## Publicar depois

O usuário optou por preparar tudo localmente. Não houve push, merge, ativação
do Pages ou execução remota do workflow nesta etapa.

1. Autenticar o Git localmente, sem colocar token nos arquivos do projeto.
2. No GitHub, selecionar a fonte **GitHub Actions** em Settings → Pages.
3. Enviar a branch de trabalho:

   ```bash
   git push -u origin dev
   ```

4. Abrir um pull request de dev para main e aguardar **Qualidade e build**.
5. Mesclar o PR; o push resultante na main dispara o deploy após os checks.
6. Conferir o job **GitHub Pages** e a URL do site. Se o ambiente pedir aprovação,
   autorizar o deployment no GitHub. Build local não substitui essa conferência.

Integrar dev à main pelo PR, sem force-push. Conferir o estado das branches no
GitHub antes da integração; os registros locais não representam seu estado atual.

## Revisão antes de enviar

```bash
git status --short
git diff --check
uv run pytest --cov
uv run mkdocs build --strict
```

Não versionar banco, CSVs/Parquets originais, backups, caches, credenciais ou
AGENTS.md. Não fazer force-push ou reescrever os commits para simular etapas.
Estados de CI/deploy precisam ser conferidos no GitHub; build local não prova
que o site já está publicado.
