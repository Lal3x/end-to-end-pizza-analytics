# Instruções do projeto Pizza

## Escopo atual

A Etapa Zero foi revisada e o usuário autorizou avançar. O próximo incremento
é implementar e testar o módulo de conexão conforme specs/db.md, antes da
ingestão. Continuar uma etapa por vez. Não realizar commits nem publicar sem
autorização. Não reconstruir histórico retroativamente.

## Método obrigatório

Investigar → comportamento esperado → spec prévia → critérios mensuráveis →
implementar → executar → registrar evidências e suposições → preparar commit.
Cada spec em `specs/` contém contexto, entradas, saídas, regras, proibições,
erros, critérios de aceite e motivos. Propostas não são decisões aprovadas.
Docstrings dos módulos futuros devem referenciar a spec e explicar suas regras.

## Edição

Preferir `apply_patch` para código, configuração e documentação. Explicar
exceções para arquivos gerados e resumir alterações. Não prometer exibição de
diff pela interface. Não modificar diretórios de configuração protegidos.

## Arquitetura e stack

Python 3.13, uv, DuckDB (`pizza.duckdb`), pandas quando necessário, SQL,
pytest/pytest-cov, Ruff, Streamlit e Plotly. Sem serviços ou orquestradores novos
sem justificativa e autorização. `raw/` contém os CSVs originais locais.
Schemas: `raw` → `refined` → `marts`. Preservar nomes originais nesta proposta.

- RAW: tudo VARCHAR, preservar valores e nulos; sem deduplicação ou conversão;
  verificar todas as fontes antes de gravar; substituir idempotentemente.
- REFINED: investigar antes de decidir; dinheiro DECIMAL; IDs VARCHAR; conversão
  inválida e conflito de chave falham explicitamente; nunca alterar raw.
- MARTS: um SQL numerado por pergunta, grão no comentário inicial, somente
  refined como fonte; executor sem fórmulas; transação única e rollback;
  mart obrigatório vazio causa falha.
- Dashboard futuro: rascunho antes do visual; somente SELECT em marts, conexão
  read_only fechada após leitura; sem groupby/merge de negócio na apresentação.

## Validação

Testes em `test/` com exemplos sintéticos, DuckDB real temporário e asserts;
usar tmp_path/monkeypatch quando necessário. Sem CSV real, banco do projeto,
rede obrigatória, mocks do DuckDB, skips artificiais ou números copiados da base.
Meta de cobertura Python relevante ≥60%. Qualidade real é verificada à parte:
PK, FK, nulos, domínios, tipos, grão e reconciliações exatas em dinheiro.

## Relato e publicação

Cada etapa relata arquivos, decisões, comandos executados, resultados, testes,
critérios atendidos/pendentes, problemas, suposições e próximo passo. Não inventar
execuções ou erros da IA. Conferir licença da fonte efetivamente baixada antes
de publicar dados. Dados e banco ficam fora do Git por padrão.
