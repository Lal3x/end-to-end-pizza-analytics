# Decisões técnicas e limitações

## Condução do projeto

O autor criou e validou as especificações, tomou as decisões de negócio e
definiu os indicadores do projeto. Também conduziu a escolha da fonte, o escopo,
a arquitetura e a validação dos resultados. O Codex atuou como ferramenta de
apoio à investigação, ao detalhamento dos contratos, à implementação e aos testes,
sob orientação e revisão do autor.

| Decisão do autor | Aplicação no projeto |
| --- | --- |
| Criar e validar as specs antes da implementação | Contratos com entradas, saídas, regras, motivos e critérios de aceite para cada etapa |
| Definir as perguntas de negócio e os indicadores | Fórmulas, grãos, fontes e regras de inclusão documentados nos contratos e implementados nos SQLs dos marts |
| Escolher Pizza Paradise e definir o recorte analítico | Análises de clientes e lojas, além de pedidos e produtos, com contratos específicos para cada grão |
| Corrigir o excesso de módulos e exigir transformação com pandas | pipeline/ contém somente ingestão, transformação e executor de marts; conexão e aquisição ficam na raiz |
| Manter nomes originais e identificadores textuais | Rastreabilidade entre fontes, refined e SQLs, sem renomeações desnecessárias |
| Aprovar regras de transformação antes da implementação | Precisão temporal explícita, correção restrita da vírgula terminal de Launch em PZ026/PZ027 e tolerância monetária de até 1e-9 para ruído de representação |
| Solicitar Pareto e separar análise de SKU da consolidação por nome | Contratos distintos para variantes e tipos de pizza; concentração calculada no SQL |
| Revisar o Pareto e escolher horário de São Paulo | Eixo com nomes dos produtos; mart horário em America/Sao_Paulo |
| Definir identidade visual ciano e exigir números reais no rascunho | Protótipo e PNG com valores consultados dos marts antes da implementação Streamlit |
| Solicitar executor completo, CI, pre-commit e documentação publicável | Execução transacional das etapas e verificações automatizadas; publicação remota adiada por escolha do autor |

As aprovações foram específicas à fonte e à etapa. Na fonte atual, ocorrências
repetidas de order_items representam unidades legítimas e são preservadas.
A moeda de Pizza Paradise não está comprovada nos anexos: o painel exibe a
unidade monetária original sem símbolo não documentado.

## Critérios técnicos

- RAW preserva valores, nulos e multiplicidades; CSV textual e Parquet nativo.
- REFINED valida chaves, conversões e relações; dinheiro em DECIMAL(18,2).
- Cada indicador tem SQL próprio, grão declarado e fonte somente refined.
- Dashboard consulta marts em modo de leitura, sem recalcular indicadores.
- Testes usam exemplos sintéticos e DuckDB temporário; auditorias conferem a fonte real separadamente.

## Limitações da análise

Os dados são fictícios. Não existem custos, status ou eventos logísticos que
sustentem margem, cancelamento ou prazo. São Paulo é referência escolhida para
visualização das horas, não o fuso comercial comprovado das lojas. Mês e dia da
semana seguem a data original; 116 pedidos sem hora não recebem horário inventado.
A fonte tem permissão textual ampla, sem licença padronizada nos metadados;
os anexos completos e o banco não são redistribuídos.

## Participação da IA e revisão humana

O autor identificou a estrutura excessiva e a transformação SQL que contrariavam
a arquitetura desejada; pediu a simplificação e o uso de pandas. Também apontou
rótulos pouco claros no Pareto e falta de docstrings, solicitando as correções.
Essas intervenções alteraram a implementação e a apresentação do projeto.

Nas execuções assistidas, a inferência de precisão Decimal do DuckDB falhou com
um valor posterior à amostra. A correção declarou DECIMAL(18,2) explicitamente e
incluiu teste sintético. Formatos de data e repetições legítimas de itens foram
investigados antes de consolidar as regras. A revisão humana das propostas e os
checks automatizados têm papéis complementares.

Algumas mudanças ficaram acumuladas antes dos commits; o histórico real foi
preservado, sem retrodatação. Os detalhes estão no [registro metodológico](metodologia.md).
Fonte, grãos e fórmulas: [permissão](fontes-e-licenca.md), [modelo](modelo.md) e
[contratos](contratos-indicadores.md). Execuções e resultados: [arquivo técnico](historico.md).
