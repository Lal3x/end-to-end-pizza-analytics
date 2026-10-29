# Avaliação do Pizza Paradise — alternativa à base atual

Data: 28/10/2026. Investigação independente; nenhuma migração aprovada ou
executada. O pipeline atual e pizza.duckdb não foram abertos ou alterados nesta
avaliação. Os SELECTs de transformação preparados anteriormente permanecem
pendentes de validação, devido ao bloqueio do banco pela UI.

## Fonte e acesso efetivamente realizado

- [Notebook oficial da Observable](https://observablehq.com/@observablehq/pizza-paradise-data),
  documento `0522fa2e9659bee6`, versão 398, atualizado em 27/07/2023.
- [Código público do notebook](https://api.observablehq.com/@observablehq/pizza-paradise-data.js?v=3),
  consultado para localizar os anexos e ler a descrição do publicador.
- [Metadados públicos](https://api.observablehq.com/document/@observablehq/pizza-paradise-data),
  consultados para conferir versão, autoria e campo de licença.

O autor descreve os dados como inteiramente fictícios, gerados pela equipe
Observable para demonstração. Não representam uma rede real nem comportamento
medido de consumidores. Foram baixados cinco anexos originais, sem usar os
agregados prontos do notebook. Os arquivos ficaram em
`/tmp/pizza-paradise-inspecao/`, fora das fontes do projeto.

As respostas dos três CSVs vieram comprimidas com gzip, apesar da extensão .csv.
O primeiro leitor falhou; o cabeçalho binário gzip foi identificado e cópias
descomprimidas foram geradas para leitura. Os dois Parquets têm assinatura PAR1.
Os bytes baixados e descomprimidos têm hashes registrados separadamente na
[evidência de inspeção](evidencias/pizza-paradise-inspecao.json), gerada pela
auditoria. A extração e o JSON foram produzidos por ferramentas, sem edição
manual de dados. Esta evidência contém somente perfis, não as bases completas.

## Comparação medida

| Aspecto | Fonte atual | Pizza Paradise inspecionado |
|---|---|---|
| Pedidos | 21.350 | 2.046.713 |
| Linhas de itens | 48.620 | 2.916.015 |
| Produtos/variantes | 96 variantes, 32 tipos | 36 SKUs, 9 nomes, 4 tamanhos |
| Clientes identificados | Ausentes | 34.761 |
| Lojas identificadas | Ausentes | 32 |
| Período | 2015 | 01/01/2020 a 31/12/2022 |
| Fontes principais | Quatro CSVs | Três CSVs e dois Parquets |
| Receita no pedido | Não disponível | total, reconciliável com os itens |
| Dados geográficos | Ausentes | Coordenadas de clientes/lojas; cidade e estado de lojas |

Os cinco downloads originais somam aproximadamente 33,5 MB em bytes; as cópias
descomprimidas dos CSVs são adicionais. O volume não exigiu trocar Python/uv/
DuckDB por outra stack: a auditoria executou consultas locais no ambiente atual.
CSV foi lido com inferência somente para investigação; isso não define como
uma nova camada RAW deverá preservar os tipos originais.

## Modelo observado

| Tabela | Colunas | Grão e ligação |
|---|---|---|
| orders | id, customerId, storeId, orderDate, nItems, total | Um pedido; id único; referências a customers e stores |
| order_items | SKU, orderID | Ocorrência de produto no pedido; referências a products e orders; sem ID próprio de linha |
| products | SKU, Name, Price, Category, Size, Ingredients, Launch | Um SKU; chave única |
| customers | id, latitude, longitude | Um cliente fictício; id único |
| stores | id, zipcode, state_abbr, latitude, longitude, city, state, distance | Uma loja; id único; significado de distance ainda não documentado |

Relações verificadas: orders.customerId → customers.id; orders.storeId →
stores.id; order_items.orderID → orders.id; order_items.SKU → products.SKU.
Zero órfãos nas quatro relações. Zero nulos em todas as colunas e nenhuma PK
repetida em orders, customers, stores ou products. Todo pedido tem itens.

## Problemas e decisões de tratamento que os dados realmente exigem

### Repetição de item não é duplicata descartável

Há 54.041 linhas repetidas além da primeira em order_items e 53.462 grupos
(orderID, SKU) com repetição. Um pedido pode ter até quatro ocorrências do mesmo
SKU. Preservando essas linhas, COUNT de itens por pedido coincide com nItems em
todos os pedidos. Removendo-as, 53.275 pedidos deixam de coincidir com nItems.

Logo, a política atual de eliminar linhas exatas em refined não pode ser
transferida para essa tabela. A repetição representa multiplicidade necessária
à reconciliação, não há quantidade explícita nem ID que permita descartá-la.
Uma eventual migração deve definir identidade/rastreabilidade da linha e se a
refined preserva ocorrências ou agrega quantidade por pedido/SKU.

### Datas com precisões diferentes

- 2.012.617 pedidos: data/hora com segundos e Z, 20 caracteres.
- 33.980 pedidos: data/hora até minutos e Z, 17 caracteres.
- 116 pedidos: somente data, dez caracteres.

CAST direto para TIMESTAMPTZ falhou nos 33.980 registros sem segundos nesta
versão do DuckDB. Diagnóstico com formatos explícitos `%Y-%m-%dT%H:%M:%SZ`,
`%Y-%m-%dT%H:%MZ` e `%Y-%m-%d` reconheceu todas as entradas.
Isso não aprova preencher hora ausente com meia-noite: a origem não comprova
se os 116 registros são eventos à meia-noite ou perda de precisão. Análises
horárias precisariam de regra e indicação de precisão explícitas.

### Launch com pontuação extra

PZ026 e PZ027 trazem Launch = `2020-01-01,`. O CAST do DuckDB aceita esse texto,
mas a comparação com o formato canônico revelou a vírgula. Isso exige uma
correção documentada, não uma conversão permissiva silenciosa.

### Dinheiro e reconciliação

orders.total vem como DOUBLE no Parquet; products.Price é texto numérico no
CSV, inferido como DOUBLE na investigação. Ao converter ambos para
DECIMAL(18,2), a soma dos preços das ocorrências de itens coincide com o total
de cada um dos 2.046.713 pedidos: zero divergências. COUNT de itens também
coincide com nItems em todos eles. Preços/totais não negativos e finitos.

Essa verificação foi feita após normalização a centavos; não demonstra histórico
de preços, ausência de arredondamento na geração ou política de impostos.
Não atribuir automaticamente a aprovação de moeda USD da fonte anterior a esta
nova fonte: a moeda e o significado de total devem ser formalizados na nova spec.

## Análises adicionais sustentadas ou candidatas

- Recompra/frequência por customerId: 19.734 clientes têm mais de um pedido.
- Vendas por loja, cidade e estado da loja, com receitas e períodos comparáveis.
- Evolução anual e comparação entre 2020, 2021 e 2022.
- Reconciliação de total/nItems do pedido com os itens por dois caminhos.
- Concentração de vendas por loja e cliente, além de produtos.
- Análise geográfica usando coordenadas; distância calculada exigiria definição
  própria e não pode ser confundida com rota percorrida ou tempo de entrega.
- Lançamento de produtos: candidato, após resolver Launch e conferir datas.

Não há campos de custo, pagamento, cancelamento ou eventos de entrega nas cinco
tabelas. Portanto, continuam sem suporte lucro, margem, atraso e cancelamento.
Customers tem apenas ID e coordenadas: não inventar perfil demográfico.

## Licença e atribuição: evidência e pendência

O texto do notebook permite uso amplo do conjunto fictício. A frase exata está
no campo source.permission_text do JSON de evidência. Entretanto, os metadados
retornam `license: null` e não foi identificada licença padronizada específica
para todos os anexos. Isso deve ser documentado como permissão textual do
publicador, sem rotular o conjunto como CC0 ou ISC por inferência.

O [repositório de amostras](https://github.com/observablehq/sample-datasets)
tem licença ISC e um pizza.csv, mas isso não comprova por si só a licença dos
cinco anexos baixados do notebook. Não houve redistribuição dos arquivos.
Antes de publicar dados completos numa migração, esclarecer os termos aplicáveis
a esses anexos e manter atribuição à Observable/equipe geradora e Paul Buffa.

## Parecer

Para o objetivo adicional de trabalhar maior volume, clientes, várias lojas e
tratamentos com decisões reais, o Pizza Paradise é mais rico que a fonte atual.
Não é apenas aumento artificial de linhas: há novas entidades, três anos e
problemas observados de granularidade e representação temporal.

Para terminar o desafio com menor esforço, a fonte atual continua suficiente.
Uma troca exige nova investigação/specs de ingestão e transformação, política
de repetição de itens, tipos monetários, datas e grãos dos indicadores. Não é
compatível substituir arquivos e reaproveitar as regras atuais sem revisão.
Os arquivos Parquet também exigem rever o contrato de RAW desenhado para CSVs.

Recomendação: se a prioridade do usuário é ampliar a profundidade deste projeto,
considerar migração após resolver a documentação de licença e revisar a Etapa
Zero da nova fonte. Preservar o histórico atual; não há troca automática nesta
avaliação. Não é necessário introduzir Spark, Docker, nuvem ou outro banco.

## Execução e limites desta avaliação

Downloads públicos por curl; inspeção por DuckDB em banco exclusivamente em
memória e script local `/tmp/auditar_pizza_paradise.py`; relatório gerado em
docs/evidencias/pizza-paradise-inspecao.json. Todos os registros foram usados
nas contagens, nulos, PK/FK, repetições e reconciliações. Uma tentativa de trazer
TIMESTAMPTZ para Python exigiu pytz ausente; a auditoria passou a retornar datas
como texto SQL, sem instalar dependência. Erro de CAST das datas foi registrado
e diagnosticado com formatos explícitos, sem descartar registros.

Não é teste do pipeline atual: pytest/cobertura não foram executados nem
alterados. Nenhum commit ou migração foi feito nesta investigação. O JSON e
este parecer são novos artefatos de pesquisa; os downloads temporários não
estão no repositório. Código de auditoria em /tmp é temporário; se houver
migração, a aquisição e o perfil deverão virar artefatos reproduzíveis próprios.
