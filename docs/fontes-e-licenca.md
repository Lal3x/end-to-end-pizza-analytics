# Fonte ativa, permissão e proveniência — Pizza Paradise

Fonte dos dados do projeto:
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
Nenhum envio dos cinco anexos completos à nuvem faz parte do projeto.

## Revisão de publicação — 29/10/2026

A declaração de uso foi reconferida no código do notebook oficial. A atribuição
e a distinção entre permissão textual e ausência de licença padronizada são
mantidas; isso não é uma afirmação de licença CC0/ISC nem um parecer jurídico.

Escopo da entrega pública: código autoral, specs, guias, capturas e resultados
derivados/evidências pequenas. Os cinco CSV/Parquets completos, pizza.duckdb,
backups e respostas originais de aquisição permanecem locais/ignorados. O
downloader obtém os anexos do publicador, não de uma cópia distribuída pelo repo.
Essa política também vale para o artefato MkDocs/Pages, construído de docs/,
sem incluir raw/, data/, banco, credenciais ou AGENTS.md.

Uma futura redistribuição dos anexos completos exige outra revisão dos termos.
A revisão atual documenta os termos e restringe os artefatos publicados; não
converte license:null em uma licença padronizada inventada.

## Aquisição reproduzível

baixar_dados.py fixa as URLs dos cinco anexos investigados e verifica
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
