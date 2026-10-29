# Critérios de entrega

## Funcionalidade já validada

- Fonte ativa documentada e aquisição reproduzível com hashes.
- Cinco tabelas RAW e cinco refined, com grãos e relações declarados.
- Treze indicadores com SQL rastreável e reconciliação financeira.
- Executor completo com rollback do conjunto, testes de falhas e reexecução.
- Dashboard só de marts, rascunho PNG, formatos testados e recarga sem conexão global.
- 127 testes aprovados na etapa do executor, cobertura 94,81%.

[Modelo](modelo.md), [contratos](contratos-indicadores.md),
[validação completa](execucao-pipeline.md) e [painel](execucao-dashboard.md).

## Revisão final local concluída

CI, hooks e site MkDocs configurados. Em ambiente virtual novo, os 127 testes
passaram com cobertura de 94,81%; o build estrito da documentação passou.
Uma nova aquisição e execução completa reproduziram as 23 tabelas sem diferenças.
O bloqueio de arquivo .env também foi verificado com um exemplo artificial.
[Evidências da automação](execucao-automacao.md).

Por escolha do usuário, publicação fica para depois: não houve push, execução
remota do workflow ou ativação do Pages. O roteiro está em [automação](automacao.md).

## Fonte e limites

O publicador permite uso amplo em texto, sem licença padronizada nos metadados.
Mantemos atribuição e os arquivos completos fora do repositório. Código, guias,
imagens e resultados derivados são os artefatos de entrega, sem redistribuir
os cinco anexos originais. [Permissão e proveniência](fontes-e-licenca.md).

Sem custos/status/eventos logísticos, não afirmar margem, cancelamento ou prazo.
Moeda não declarada nos anexos; São Paulo é referência de visualização, não o
fuso comercial das lojas. Dados são inteiramente fictícios.

## Git e autoria

O histórico real é preservado. Algumas alterações ficaram acumuladas antes de
serem registradas; isso está explicado na [metodologia](metodologia.md), sem
retrodatação. A participação da IA inclui somente problemas efetivamente vistos.
O repositório pessoal é público; CI e Pages ainda precisam ser conferidos após
o envio das configurações. AGENTS.md e dados locais permanecem ignorados.
