# Migração para Pizza Paradise

Status: aquisição/ingestão migradas e validadas; specs registradas antes do código.
Ingestão é o incremento atual; transformação, marts e dashboard continuam
sujeitos a suas validações intermediárias.

## Contrato e preservação

Manter todos os arquivos Maven locais e uma cópia por hash do banco anterior.
A nova aquisição usa raw/pizza_paradise/ e a carga de ensaio usa banco separado.
Após validar, substituir somente RAW em pizza.duckdb numa transação.
Não apagar o histórico ou reapresentar os resultados anteriores como novos.

Diferenças registradas antes do código: cinco fontes; CSVs texto e Parquets
tipados na RAW; itens sem PK natural preservando ocorrências; três formatos
temporais, correção Launch proposta e moeda ainda não comprovada nos anexos.
Permissão textual do publicador documentada, sem redistribuição dos anexos.

Os quatro SELECTs Maven preparados mas nunca executados foram retirados da
pasta ativa sql/transformacao: não se aplicam a Pizza Paradise. Nenhuma refined
Maven foi publicada. A avaliação e seu JSON passam a integrar a fundação da
migração. Resultados efetivamente executados estão abaixo.

## Artefatos implementados

- pipeline/fontes.py: nomes, colunas, tipos Parquet, URLs e hashes fixados.
- pipeline/aquisicao.py e scripts/baixar_paradise.py: aquisição e validação
  integral antes de publicar os cinco arquivos; gzip de transporte tratado
  sem editar campos; respostas originais e manifesto ficam em data/.
- pipeline/ingestao.py: preflight com CSV estrito e metadados Parquet;
  apenas CSVs pequenos em pandas, fatos diretamente em DuckDB;
  opção --banco; recriação de raw atômica, sem tabelas Maven remanescentes.
- scripts/auditar_paradise.py: verificação independente somente leitura usando
  EXCEPT ALL em ambos os sentidos, tipos/colunas/hashes/FKs e ocorrências.
- test/test_ingestao.py atualizado; test/test_aquisicao.py criado; testes de
  conexão preservados. README e plano atualizados; AGENTS.md segue local.

## Comandos e resultados observados

1. Commit 67da898 registrou modelo, fonte, indicadores e specs da migração
   antes da implementação. Pequena adição prévia na spec explicitou módulos
   compartilhados de fontes/aquisição antes de criar esses arquivos.
2. Ruff format ajustou layout de código/testes; Ruff check --fix organizou
   imports do script fino. Exceção de edição: ferramentas automáticas apenas
   para formatação/imports; demais mudanças por apply_patch.
3. .venv/bin/pytest --cov: 26 testes passaram em 2,83 s; 155 linhas, duas
   não cobertas (limite de tamanho HTTP e entrada CLI), cobertura total 98,71%.
   Sem falhas funcionais; duas linhas longas em testes foram corrigidas por patch.
4. uv run python scripts/baixar_paradise.py: cinco anexos conferidos por SHA-256,
   publicados em raw/pizza_paradise; originais e manifesto em
   data/pizza_paradise/recepcao-*/. Rede somente na aquisição, não nos testes.
5. /usr/bin/time -v .venv/bin/python -m pipeline.ingestao --banco
   data/pizza-paradise-validacao.duckdb: saída zero, 2,59 s, RSS máximo
   588.552 KiB (aprox. 575 MiB), zero swap. Os CSVs pequenos passam por pandas;
   os milhões de linhas Parquet não são convertidos em DataFrames Python.
6. Auditoria no banco de ensaio, reexecução da carga e nova auditoria:
   JSONs idênticos por cmp. [Evidência de ensaio](evidencias/pizza-paradise-carga-validacao.json).
7. Banco principal ainda estava bloqueado por ui.py PID 21885, mesmo após o
   usuário informar encerramento. Verificação fora do sandbox confirmou processo
   suspenso (T); SIGINT não liberou o arquivo. Encerramento autorizado com
   SIGTERM/CONT resolveu o bloqueio. Nenhuma carga principal foi feita antes disso.
8. CHECKPOINT do banco Maven e cópia binária com conexão de leitura aberta:
   data/backups/maven-e8542a701d7a.duckdb. SHA-256 da cópia igual ao original;
   cópia reaberta e quatro contagens antigas confirmadas.
   [Evidência do backup](evidencias/backup-maven.json).
9. .venv/bin/python -m pipeline.ingestao no banco principal, seguido pela
   auditoria independente: sucesso. Relatórios de ensaio/final coincidem ao
   desconsiderar o caminho do arquivo de banco.
   [Evidência final](evidencias/pizza-paradise-carga-final.json).
10. Reexecução pelos comandos do README: uv run python scripts/baixar_paradise.py,
    uv run python -m pipeline.ingestao e uv run python scripts/auditar_paradise.py.
    Aquisição existente conferida sem novo download; a auditoria final repetida
    foi idêntica por cmp. Ruff check/format e git diff --check aprovados;
    todos os links locais dos documentos/specs conferidos.

## Aceite da ingestão

orders 2.046.713; order_items 2.916.015; customers 34.761; stores 32; products
36; total 4.997.557. Quatro FKs sem órfãos. Zero diferenças EXCEPT ALL entre
fonte e carga: valores e multiplicidades preservados. CSVs VARCHAR e Parquets
nos tipos nativos; 54.041 ocorrências repetidas além da primeira mantidas.
Somente cinco tabelas da nova fonte em raw; tabelas legadas foram removidas
pela substituição transacional. Fontes Maven e cópia do banco estão preservadas.

Testes sintéticos cobrem dois itens iguais no mesmo pedido, tipos Parquet,
zeros/nulos/tokens/espaços/textos CSV, fonte ausente, encoding/cabeçalho/registro
inválido, Parquet inválido, tipo/coluna divergente, nova carga em banco separado,
recusa com refined/marts existentes, e páginas corrompidas cujo footer é válido
(erro após iniciar carga, com rollback comprovado). Aquisição testa gzip,
hash divergente, publicação sem parcialidade e não sobrescrever fonte alterada.

## Pendências e próximo incremento

Refined, marts e dashboard não foram implementados; não há resultado financeiro
novo apresentado como indicador do projeto. Permanecem para revisão: moeda,
precisão monetária de DOUBLE, campos temporais derivados e correção Launch.
Redistribuição dos anexos completos continua pendente de esclarecimento da
permissão; os dados e backups ficam ignorados. Nenhuma suposição adicional de
negócio foi implementada. Próximo: SELECTs de investigação da nova RAW e revisão
dos resultados antes de codificar a transformação.
