# Referências analisadas e adaptação

As quatro páginas foram efetivamente acessadas por `curl -L --fail` em
2026-10-28. O navegador de pesquisa retornou erro interno para as aulas; o
primeiro curl no sandbox falhou por DNS. A repetição com acesso autorizado
funcionou para todas. O HTML foi extraído com HTMLParser para leitura do conteúdo
principal, incluindo specs. Nenhum código do curso foi copiado.

| Referência | Método observado | Aplicação proposta neste projeto |
|---|---|---|
| [Aula 1](https://ckoliveiraa.github.io/pipeline-olist/aula-1.html) | uv bare, DuckDB local, raw fiel em texto, decisão → spec → código → conferência; ingestão idempotente | Configuração sem build-system; arquivos → quatro tabelas raw; verificar tudo antes de gravar; contar no destino |
| [Aula 2](https://ckoliveiraa.github.io/pipeline-olist/aula-2.html) | Investigar nulos, duplicatas, tipos e chaves antes de limpar; dinheiro DECIMAL, IDs texto, conversões explícitas, antes/depois | Datas reais são dia/mês/ano; encoding distinto por arquivo; nenhuma limpeza artificial; conflito de PK interrompe |
| [Aula 3](https://ckoliveiraa.github.io/pipeline-olist/aula-3.html) | Pergunta e grão antes do JOIN; CTE para ajustar grão; SQL numerado, executor sem regra; recriação transacional, vazio falha, reconciliação | Uma linha de item permanece uma linha após N:1; receita por quantidade × preço; receita por pedido antes do ticket; dez marts candidatos |
| [Aula 4 / desafio](https://ckoliveiraa.github.io/pipeline-olist/aula-4.html#desafio) | Rascunho antes do painel; apresentação só SELECT; leitura read_only fechada; testes sintéticos versus qualidade real; cobertura ≥60%; histórico incremental autoral | Dashboard só após validar marts, módulos painel/app separados; test/ e DuckDB temporário; publicação e commits após aprovação |

## Decisões que não são transferíveis da Olist

O grão da pizzaria não vira “um pedido” em todas as tabelas: item, variante e
tipo têm grãos próprios. Receita exige multiplicar quantidade por preço,
diferentemente do preço por item no exemplo Olist. Não existem status de pedido,
frete, clientes ou avaliações para reproduzir filtros ou indicadores da Olist.
Dinheiro será apresentado em USD conforme o dicionário, não em reais.
Deduplicação não será aplicada apenas por aparecer na aula: o dado observado
não tem duplicatas. A spec de transformação é proposta sujeita à revisão.

## Identificação dos conteúdos acessados

SHA-256 do HTML baixado (cópias de leitura em `/tmp/pizza-aula-N.html`):

| Aula | SHA-256 |
|---|---|
| 1 | `73ee3c5c78c593c8b54b219f5445c61bf924449f35e75dd271b364fc9e4c7560` |
| 2 | `2067e045f26af8279880ca5f678028dcd9ed067bd497bc6e4db315b63d98758b` |
| 3 | `0929342628562d2e6326983c459f385de5c3232a29990fea1832a34eef468921` |
| 4 | `8056ac74f3cd99b100cfde380db6e735ab113cb95ac45c4d37988c32001e7051` |

Os hashes identificam a consulta, não congelam a versão futura do site.

## Correção de aderência após revisão do usuário

A primeira versão dos documentos adotou seções genéricas e uma tabela de
contratos em indicadores.md. Isso não reproduzia o formato pedido pelas aulas.
Na revisão, os exemplos locais das aulas 1–3 foram relidos e a página
[Indicadores da turma](https://ckoliveiraa.github.io/pipeline-olist/indicadores.html),
vinculada pelas aulas, também foi acessada por curl para comparação.

Correções concretas:

- `indicadores.md`: dez linhas “indicador — tabelas (colunas) — o que mede”,
  oito cruzando tabelas; hipóteses pendentes marcadas com `?` e explicadas.
- Definições e contratos preservados em `docs/contratos-indicadores.md`.
- Specs de implementação: CONTEXTO, STACK, O QUE JÁ EXISTE, ARTEFATO A PRODUZIR,
  SPEC numerada, CRITÉRIOS DE ACEITE e ENTREGA, com motivos junto às regras.
- Ingestão segue as sete regras da aula 1; transformação segue as sete decisões
  da aula 2, com mapa completo de tipos; executor segue o contrato da aula 3.
- `specs/db.md` explicita a dependência de conexão antes da ingestão.

As diferenças próprias da pizzaria foram mantidas: encoding observado, datas
dia/mês/ano, quatro tabelas, IDs originais e receita estimada em USD. Nomes de
colunas e filtros da Olist não foram transferidos para este dado. As dependências
futuras são distinguidas dos artefatos que realmente existem na Etapa Zero.
