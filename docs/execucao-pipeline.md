# Execução completa do pipeline

Data: 29/10/2026. [Spec](../specs/execucao-pipeline.md) e
[executor](../executar_pipeline.py).

## Entrega e comandos

Uma conexão de destino e uma transação para ingestão → transformação pandas →
marts. As etapas aceitam con externo sem iniciar/confirmar/reverter transação
nem fechar a conexão recebida. Sem con, mantêm seu comportamento isolado,
inclusive o bloqueio da ingestão quando existem camadas derivadas.
O executor remove as camadas derivadas dentro da transação e confirma somente
após todas as auditorias. Nenhum cálculo/SQL de negócio foi duplicado.

```bash
uv run python executar_pipeline.py
uv run python executar_pipeline.py --banco caminho/ensaio.duckdb
```

Na sessão foram usados .venv/bin/python e /usr/bin/time -v: ensaio em banco
novo, reexecução nesse banco e carga final em pizza.duckdb. As três terminaram
com estado publicado e JSON somente depois do commit. Sem download ou nova
dependência. A pré-validação compartilhada da ingestão ocorre antes de abrir
o destino e é repetida pela etapa; Parquets são validados em memória separada.

| Execução | Duração interna | Pico RSS do processo |
|---|---:|---:|
| Ensaio novo | 66,650 s | 1.856,51 MiB |
| Reexecução do ensaio | 66,000 s | 1.819,49 MiB |
| Banco principal | 53,848 s | 1.931,85 MiB |

Medições desta máquina, incluindo pandas/DuckDB; zero swap. Cargas sequenciais,
após concluir a suíte de testes. Não são limites fixos para outra fonte/máquina.

## Resultados e preservação

Cinco RAW e cinco refined: 2.046.713 pedidos, 2.916.015 ocorrências de itens,
34.761 clientes, 32 lojas e 36 produtos por camada. Treze marts publicados.
Não somar linhas entre camadas/grãos como se fossem pedidos ou vendas.

As 23 tabelas foram comparadas com EXCEPT ALL nos dois sentidos e DESCRIBE:
reexecução × primeira carga; ensaio × principal anterior; principal atualizado ×
ensaio; principal atualizado × backup. Zero diferenças de valores, tipos ou
multiplicidades. Auditorias de FKs, quantidade e receita aprovadas.
[Evidência completa](evidencias/execucao-pipeline.json).

Antes da carga principal, cópia local preservada em
data/backups/pipeline-completo-20261029-b234ba99.duckdb, com SHA-256 igual ao
arquivo original naquele instante, registrado na evidência. Foi backup de
verificação, fora do executor e do Git; não uma rotina automática de backup.

Schemas/objetos externos conferidos contra o backup. Não havia tabelas externas
às camadas no principal desta sessão. Preservação de conteúdo externo testada
com pessoal.notas em banco sintético, tanto em sucesso quanto em falha; não se
afirma teste com notebooks reais ausentes.

## Testes e problemas observados

127 testes passaram em 35,12 s; cobertura 94,81% de 617 linhas. Quinze testes
novos: ordem/resultado completo, reexecução por conteúdo/tipos/multiplicidades,
pré-validação, erro real de conversão, erro SQL após transformação, destino
novo/existente, schema externo, conexão emprestada, parâmetros conflitantes,
proteção da ingestão isolada, CLI e Ctrl+C/saída 130. Os 112 anteriores também
passaram. Ruff check, format check e git diff --check aprovados.

CSV/Parquet sintéticos, DuckDB temporário real, sem rede/banco do projeto ou
mocks do DuckDB. O primeiro comparador tentou fetchall de TIMESTAMPTZ e encontrou
ausência do adaptador opcional pytz. Passou a comparar linhas via JSON nativo
do DuckDB e Counter, com tipos via DESCRIBE. Não houve mudança das conversões
de produção nem instalação de dependência apenas para o comparador.

Código/docs editados por patches; Ruff format ajustou layout. Perfis de tempo
e JSON de evidência foram gerados por execuções/comparações reais.

## Cuidados de operação

- Obter as cinco fontes com baixar_dados.py antes da primeira execução.
- Encerrar ui.py; o executor não fecha processos nem contorna locks.
- Reservar memória/disco para uma transação longa; não modificar fontes/SQLs
  ou iniciar outra carga enquanto a execução está em andamento.
- O Streamlit pode ficar aberto entre leituras, mas recarga durante a escrita
  pode gerar conflito. Clicar em Recarregar dados depois de concluir.
- Rollback cobre falhas tratáveis, não substitui proteção contra disco/energia.
  Destino preexistente nunca é removido; destino novo só é limpo se sua criação
  e identidade de arquivo forem confirmadas, após fechar a conexão.

Não há retomada parcial, retries ou publicação externa. Nenhum commit novo
foi criado nesta etapa; alterações prontas para revisão.
