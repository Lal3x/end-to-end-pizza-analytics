# Fonte, licença e proveniência

Consulta realizada em 2026-10-28. Fonte efetivamente baixada:
[Kaggle — Neethi Mohan, Maven Pizza Challenge Dataset](https://www.kaggle.com/datasets/neethimohan/maven-pizza-challenge-dataset),
referência `neethimohan/maven-pizza-challenge-dataset`, versão 1.

## Evidência da republicação utilizada

A [API pública de listagem do Kaggle](https://www.kaggle.com/api/v1/datasets/list?search=maven-pizza-challenge-dataset)
retornou para **essa referência exata**:

- `id`: 2523234; `creatorName`: Neethi Mohan.
- `currentVersionNumber`: 1.
- `lastUpdated`: `2022-10-04T14:02:59.427Z`.
- `licenseName`: `CC0: Public Domain`.

A resposta integral está em [evidencias/kaggle-list.json](evidencias/kaggle-list.json).
Ela contém também outros resultados de busca: suas licenças não foram usadas.
O ZIP não contém arquivo próprio de licença; a evidência disponível é a declaração
da plataforma para a versão corrente, que coincide com a versão 1 baixada.

A [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) permite copiar,
modificar e distribuir a obra, inclusive comercialmente. Essa é a licença
declarada pelo publicador; não foi feita auditoria independente de titularidade.
Não inferimos a licença desta republicação a partir de outra fonte.

## Fonte original e limite da página

A [Maven Analytics](https://mavenanalytics.io/data-playground/pizza-place-sales)
descreve vendas anuais de uma pizzaria fictícia e declara `Public Domain`.
O download atual nessa página exige login. Sua apresentação também mostra
metadados aparentemente inconsistentes com o ZIP (499 registros e 25 campos,
com rótulos de geografia/viagens/clima). Por isso, nem contagens nem colunas
foram tomadas dessa página; foram medidas no arquivo Kaggle.

## Aquisição e integridade

Endpoint utilizado:
`https://www.kaggle.com/api/v1/datasets/download/neethimohan/maven-pizza-challenge-dataset?datasetVersionNumber=1`.

ZIP local: `data/pizza-kaggle-v1.zip`; SHA-256:
`a10880d056b5b2f5cd637bd5b435ae3f0f38e76dbc9b0e62fde4313e4a880317`.
Os cinco membros foram extraídos para `raw/` sem edição. Hashes individuais,
tamanhos e perfis estão em [evidencias/inspecao.json](evidencias/inspecao.json).
O quinto CSV é dicionário (15 linhas), não uma quinta tabela de vendas.

Decisão proposta: publicar código, documentação e inventário; manter ZIP, CSVs e
banco fora do Git. A licença declarada foi verificada, mas nenhuma publicação
foi realizada. A autorização de publicação continua pendente.

Atribuição a manter no README: “Dados: Neethi Mohan / Kaggle, Maven Pizza
Challenge Dataset v1, CC0: Public Domain; contexto original: Maven Analytics,
Pizza Place Sales. Consulta em 28/10/2026.” Não implica endosso das fontes.
A licença dos dados não atribui automaticamente uma licença ao código autoral;
essa escolha fica para a preparação da publicação.
