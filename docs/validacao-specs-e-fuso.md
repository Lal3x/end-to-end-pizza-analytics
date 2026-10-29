# Revisão das specs, Pareto e fuso horário

Data: 29/10/2026. Autorização: identificar produtos no eixo do Pareto, usar
horários de São Paulo e padronizar os contratos das specs. Não inclui Streamlit
nem commits nesta revisão.

## Conclusão da comparação

Havia diferenças reais de organização: Etapa Zero ainda tinha seções genéricas;
dashboard misturava contexto/stack e regras sem separar leitura, layout e formato;
transformação juntava nomes/tipos e não separava suas decisões de tratamento.
A spec de marts também misturava seu contrato de execução com regras analíticas.

As sete specs foram conferidas e passaram a ter os blocos, nesta ordem:
CONTEXTO, STACK, O QUE JÁ EXISTE, ARTEFATO(S) A PRODUZIR, SPEC, CRITÉRIOS DE
ACEITE e ENTREGA. Cada decisão inclui motivo; docstrings, erros, validação e
suposições estão previstos na entrega. Nenhuma regra aprovada foi substituída
por regras de outro domínio.

| Spec | Organização conferida/ajustada |
|---|---|
| etapa-zero | Blocos comuns; recorte Maven mantido explicitamente histórico |
| db | D1–D4: caminhos, responsabilidades, gravar, conexão/erro |
| ingestao | Sete tópicos: escopo, proibições, reexecução, leitura, tipagem, saída, erro |
| transformacao | Sete decisões: escopo, nomes, tipos, conversão, duplicatas, nulos, saída |
| marts | Quatro tópicos: escopo, um arquivo/uma tabela, saída, erro; qualidade em subregras |
| ui | Regras U numeradas, abertura, extensão, Ctrl+C, separação, saída/erro |
| dashboard | Leitura, nenhum cálculo, layout, formato, filtros, cache/erro |

A revisão do dashboard também explicita funções puras de formato, figura Plotly
por gráfico, separação painel.py/app.py, width="stretch", cache e botão de recarga
para a implementação futura. Não afirma que essa aplicação já existe.

## Adaptações que continuam explícitas

- db.py na raiz e apenas etapas em pipeline/, por solicitação do usuário.
- Transformação pandas em um módulo.
- CSV textual e Parquet tipado na RAW, conforme fonte e migração aprovadas.
- Preservação das repetições legítimas de itens, conforme seu grão.
- Treze arquivos obrigatórios, correspondentes aos contratos deste projeto;
  não aceitar silenciosamente apenas 12 se um obrigatório for apagado.
- Transformação/marts imprimem JSON de diagnóstico; ingestão mantém uma linha
  por tabela e total.
- Período completo e alternância de série mensal, sem filtro global; moeda sem
  símbolo não comprovado. Relatório HTML futuro continua condicionado ao escopo.

O padrão seguido é contrato explícito, motivos, aceite verificável e separação
de responsabilidades, adaptados aos dados e às escolhas do usuário.

## Pareto e horários

O eixo X agora mostra os nove nomes originais inclinados. A ordem por receita,
o acumulado e o grupo de 80% continuam vindo do mart, sem recálculo na tela.
HTML e PNG desktop/móvel foram regenerados e inspecionados. A verificação do
navegador compara os nomes com o snapshot e detecta nomes cortados no SVG.

“UTC de São Paulo” foi tratado como fuso America/Sao_Paulo, UTC−03:00 no período
2020–2022. UTC em si não muda; o SQL do mart horário converte o instante UTC
para essa referência e publica hora_local/fuso_horario. A refined conserva
order_timestamp UTC e order_date original. Somente horas mudam; dia da semana
e mês continuam pelo calendário da fonte, como sinalizado no painel.

São Paulo é referência de visualização escolhida, não o fuso comercial das lojas
americanas. Datas sem hora não recebem horário nem sofrem deslocamento.
O pico é 21h de São Paulo, com 430.329 pedidos; há 116 pedidos sem hora.

Ao conferir auditorias em outra sessão, identificou-se que a validação de
order_date dependia de order_timestamp::DATE, afetado pelo fuso da conexão.
Ela foi corrigida para timezone('UTC',order_timestamp)::DATE. Testes agora
conferem tanto o mart horário quanto essa auditoria com sessões UTC e Asia/Tokyo.

## Comandos e verificações reais

- .venv/bin/pytest --cov: 87 testes aprovados, cobertura 92,42% de 409 linhas.
- Após ajustar a auditoria UTC explícita, os 26 testes de marts foram reexecutados.
- .venv/bin/python -m pipeline.marts: recriou a camada com auditorias antes do commit.
- .venv/bin/python scripts/preparar_rascunho.py: snapshot atualizado.
- uv run --with playwright python scripts/capturar_rascunho.py: comparação dos
  nove marts usados pelo desenho, nomes do Pareto, hora de São Paulo, desktop,
  móvel, navegação, alternância mensal e PNGs. Zero erros JavaScript.
- Auditoria integral RAW idêntica ao registro anterior, comparando fontes por
  valores, multiplicidades, hashes e tipos. KPIs e contagens dos 13 marts iguais
  ao registro UTC anterior; somente a distribuição/schema do mart horário muda.

A cópia temporária antiga do banco não estava disponível nesta sessão. A revisão
não afirma comparação integral de todos os valores antigos dos marts: usou
KPIs/contagens registrados, auditorias independentes e testes de regras.
[Evidências](evidencias/revisao-specs-sao-paulo.json) e
[captura verificada](../design/verificacao.json).

Código/docs foram editados por patches; Ruff format ajustou layout Python.
Snapshot, PNGs e JSONs são artefatos gerados, sem editar manualmente resultados.
Nenhum dado RAW/refined foi escrito pela revisão.
