# Executar do zero

## 1. Obter o projeto

Pré-requisitos: Git, uv e acesso à internet para a instalação e o primeiro
download. A execução validada usa Linux/WSL e Python 3.13; a transformação
mede memória com resource, módulo do ambiente Unix. Windows nativo não foi validado.

```bash
git clone https://github.com/Lal3x/end-to-end-pizza-analytics.git
cd end-to-end-pizza-analytics
uv sync --locked --group docs
```

## 2. Obter as fontes oficiais

```bash
uv run python baixar_dados.py
```

O downloader verifica os hashes e mantém arquivos em raw/pizza_paradise/.
Fontes existentes divergentes não são sobrescritas. O pipeline não precisa de
conta nem token; os anexos são obtidos pela API pública do Observable.

## 3. Publicar todas as camadas

Encerre ui.py antes de escrever no banco:

```bash
uv run python executar_pipeline.py
```

Uma falha antes do commit reverte as três camadas. Para ensaio, sem alterar
pizza.duckdb:

```bash
uv run python executar_pipeline.py --banco data/ensaio.duckdb
```

Reservar memória/disco para a transação. A medição do banco principal foi
53,848 s e pico RSS de 1.931,85 MiB nesta máquina; não é promessa de desempenho.
[Detalhes e cuidados](execucao-pipeline.md).

## 4. Abrir o dashboard

```bash
uv run streamlit run app.py
```

Abrir http://localhost:8501. Após nova carga, clicar em **Recarregar dados**.
Seleções de ranking/série não alteram os KPIs do período completo. Horas em
São Paulo; dias e meses pela data original. Valores na unidade monetária da fonte.

## 5. Conferir qualidade

```bash
uv run pytest --cov
uv run ruff check .
uv run ruff format --check .
uv run pre-commit run --all-files
uv run mkdocs build --strict
```

Testes sintéticos não dependem de pizza.duckdb nem de raw/. Downloads e execução
completa são verificações separadas, fora da suíte unitária e do CI.

## Comandos individuais

```bash
uv run python -m pipeline.ingestao
uv run python -m pipeline.transformacao
uv run python -m pipeline.marts
uv run python ui.py
```

A ingestão isolada recusa refined/marts existentes. Para atualizar tudo, use
executar_pipeline.py. A UI de notebooks é ferramenta separada e mantém conexão
aberta até Ctrl+C. [Exploração DuckDB](execucao-ui.md).
