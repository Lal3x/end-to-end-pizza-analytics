# Rascunho do dashboard — verificação da aula 4

Data: 29/10/2026. [Spec](../specs/dashboard.md),
[HTML](../design/rascunho.html), [PNG desktop](../design/rascunho.png) e
[PNG móvel](../design/rascunho-mobile.png).

Atualização posterior nesta data: eixo X do Pareto com nomes e horas de São Paulo;
PNGs atuais regenerados. O relato abaixo descreve a primeira captura UTC,
incluindo suas dimensões antigas; revisão em [registro](validacao-specs-e-fuso.md).
Dimensões/hashes vigentes estão em design/verificacao.json.

## O que estava faltando e foi corrigido

O HTML referenciava dados.js, que não existia; por isso os cartões ficavam
vazios. Agora o snapshot vem de SELECTs read_only em nove marts agregados,
com conexão fechada após a leitura. Não são números digitados para decorar o
layout: são resultados reais do dataset Pizza Paradise, que é fictício.

A [aula 4, passo 4.1](https://ckoliveiraa.github.io/pipeline-olist/aula-4.html)
pede números reais, identificação do mart em cada caixa, uma frase com a
resposta de cada gráfico e exportação para design/rascunho.png. Esses pontos
foram aplicados ao desenho autoral, sem copiar os indicadores da Olist.
Também foi adicionada a visão por hora UTC, incluindo os 116 pedidos sem hora
em grupo separado, para cobrir a pergunta prevista no enunciado do projeto.

| KPI | Valor do mart |
|---|---:|
| Receita total | 50.211.527,85 |
| Pedidos | 2.046.713 |
| Unidades | 2.916.015 |
| Ticket médio | 24,53 |

Unidade monetária original, sem símbolo de moeda não comprovado. Os cartões
auxiliares mostram unidades por pedido, clientes com mais de uma compra e
produtos para atingir 80% da receita. A tela não recalcula esses indicadores.

## Artefatos e reprodução

```bash
uv run python scripts/preparar_rascunho.py
```

Esse comando gera design/dados.js e design/dados-metadados.json a partir dos
marts locais. Depois, abrir design/rascunho.html com o dados.js na mesma pasta.
O retrato é estático; uma nova carga dos marts exige regeneração e nova captura.

Para capturar novamente, o navegador é ferramenta temporária de desenho:

```bash
uv run --with playwright python -m playwright install chromium
uv run --with playwright python scripts/capturar_rascunho.py
```

Nesta sessão, o primeiro comando de geração usou .venv/bin/python; a captura
usou uv run --with playwright. Playwright e Chromium foram obtidos no cache,
sem alteração de pyproject.toml ou uv.lock. Código e documentação foram editados
por patches; Ruff format ajustou o layout dos scripts. JS de dados, metadados,
PNGs e verificacao.json são artefatos gerados pelas ferramentas.

O PNG é captura do HTML renderizado no Chromium, com dados carregados,
não uma imagem desenhada separadamente. Viewport desktop 1440 × 1024, captura
completa 1440 × 2726; móvel 390 × 844 com captura completa da página longa.
O tamanho 1440 × 1024 sugerido na aula é usado como janela; a imagem completa
mantém as seções seguintes legíveis, sem reduzir o dashboard a uma miniatura.

## Verificações executadas

- Todo o snapshot carregado no navegador foi comparado com SELECTs dos nove
  marts, por valores e multiplicidades, ignorando somente ordem de apresentação
  e a representação numérica equivalente 1.0/1 do JSON.
- Os quatro KPIs visíveis foram comparados com valores formatados diretamente
  do DuckDB, independentemente do código de formatação JavaScript.
- Sete gráficos identificam origem e medida e têm uma frase-resposta.
- Alternância receita/pedidos altera apenas o gráfico mensal; KPIs permanecem
  globais. Navegação entre seções funciona.
- Desktop e móvel sem transbordamento horizontal ou números cortados nos KPIs.
  Zero erros JavaScript; hashes dos arquivos estão em
  [design/verificacao.json](../design/verificacao.json).
- Inspeção visual do PNG detectou um rótulo de data na borda do gráfico mensal;
  o alinhamento foi corrigido e as capturas foram regeneradas.

Nenhuma etapa do pipeline foi alterada. Esta verificação usa o banco real para
conferir o artefato de desenho; não é teste unitário nem substitui os testes
sintéticos do projeto. Não houve nova execução da suíte do pipeline nesta etapa.

## O que ainda falta

1. Validação humana do desenho, incluindo o teste de leitura de cinco segundos
   sugerido na aula; automação não comprova compreensão do usuário.
2. Implementar painel.py e app.py conforme a spec aprovada, com leitura somente
   de marts, conexão read_only fechada e formatação/gráficos separados da UI.
   Este HTML é protótipo, não o dashboard Streamlit concluído.
3. Testes sintéticos de formatação/apresentação e nova medição de cobertura
   incluindo painel.py. Conferir o Streamlit no navegador e recarga após marts.
4. Relatório HTML reutilizando as funções de painel.py, se incluído na entrega.
   O protótipo atual não substitui relatorio.py/relatorio.html.
5. Versionar os artefatos e registrar commits reais; transformação e marts
   continuam sem commit. Não reconstruir artificialmente a cronologia.
6. Na revisão final: comandos do README do zero, termos de uso da fonte
   efetivamente utilizada e repositório público. Arquivos brutos não são
   liberados para publicação por esta captura.

O desafio final publicado na aula apresenta dashboard como opcional; se houver,
deve ler apenas indicadores. O escopo solicitado neste projeto inclui Streamlit
e Plotly. Logo, cumprir o PNG não encerra a entrega combinada do dashboard.

## Referência conferida

Página oficial da aula 4 acessada em 29/10/2026 por curl e extraída para leitura,
incluindo passo 4.1, spec do painel e requisitos do desafio final. O navegador de
pesquisa retornou erro interno e o primeiro curl no sandbox falhou por DNS;
o acesso autorizado funcionou. A comparação foi feita com o conteúdo acessado,
não somente com os registros anteriores do projeto.
SHA-256 do HTML consultado:
`8056ac74f3cd99b100cfde380db6e735ab113cb95ac45c4d37988c32001e7051`.
