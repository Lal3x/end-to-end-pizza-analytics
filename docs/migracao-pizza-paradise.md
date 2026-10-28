# Migração para Pizza Paradise

Status: autorizada pelo usuário; specs atualizadas antes de alterar o código.
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
migração. Resultados de código, testes e carga serão registrados após execução.
