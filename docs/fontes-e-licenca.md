# Fonte ativa, permissão e proveniência — Pizza Paradise

A migração para Pizza Paradise foi autorizada em 28/10/2026. Fonte:
[notebook oficial Observable](https://observablehq.com/@observablehq/pizza-paradise-data).
Documento 0522fa2e9659bee6, versão 398, atualizado em 27/07/2023.
Dados inteiramente fictícios, gerados pela equipe Observable; autoria do notebook
Paul Buffa. Não representam uma pizzaria real.

## Evidência de uso e limites

O publicador declara no notebook: “Feel free to use this entirely fake dataset
for anything you wish!”. Os metadados públicos retornam license: null.
Existe permissão textual ampla, mas não foi identificada licença padronizada
aplicável aos cinco anexos. Não rotular esses anexos como CC0 ou ISC.

O repositório observablehq/sample-datasets tem licença ISC e um pizza.csv;
essa licença não é automaticamente atribuída aos cinco anexos do notebook.
Desenvolvimento com arquivos locais autorizado; arquivos completos permanecem
ignorados pelo Git. Antes de redistribuir, esclarecer os termos aplicáveis.
Nenhum envio dos arquivos à nuvem faz parte do projeto.

## Aquisição reproduzível

scripts/baixar_paradise.py fixa as URLs dos cinco anexos investigados e verifica
SHA-256 de cada conteúdo canônico. CSVs podem vir com gzip de transporte:
preservar resposta original em data/pizza_paradise e descomprimir sem editar
campos. Parquets mantêm bytes/tipos nativos. Fontes ativas:
raw/pizza_paradise/{customers.csv,stores.csv,products.csv,orders.parquet,order_items.parquet}.

Referência de hashes, contagens, esquema observado e metadados:
[evidencias/pizza-paradise-inspecao.json](evidencias/pizza-paradise-inspecao.json).
A avaliação documenta as relações e os problemas encontrados:
[avaliacao-pizza-paradise.md](avaliacao-pizza-paradise.md).

Atribuição: “Pizza Paradise, dados fictícios gerados pela equipe Observable;
notebook de Paul Buffa, versão 398. Consulta em 28/10/2026.”

## Fonte anterior

A versão Maven/Kaggle permanece nos commits anteriores e nos registros
execucao-etapa-zero.md, execucao-db.md e execucao-ingestao.md. Seus arquivos e
banco anterior serão preservados localmente. Sua declaração CC0 não se transfere
ao Pizza Paradise. As contagens anteriores não são resultados da nova ingestão.
