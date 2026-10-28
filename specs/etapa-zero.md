# Etapa Zero — contrato prévio

Status: contrato histórico da fonte Maven, substituído pela migração autorizada
para Pizza Paradise. Ver docs/plano.md e specs/ingestao.md para a fonte ativa.
Data original: 2026-10-28.

## Contexto e objetivo

Investigar a fonte indicada e preparar um projeto autoral com especificações
anteriores ao código. Esta etapa termina antes da implementação do pipeline.

## Entradas e dependências

- Kaggle `neethimohan/maven-pizza-challenge-dataset`, versão 1, e página Maven.
- Python, uv, acesso público às fontes; nenhum token ou conta obrigatório.

## Saídas esperadas

AGENTS.md, README, avaliação de fonte/licença, modelo relacional, indicadores,
plano, propostas iniciais de specs, configuração do ambiente e evidência de
inspeção reproduzível. Script de inspeção lê o ZIP sem modificá-lo e emite JSON:
hashes, encoding, colunas, contagens, vazios, duplicatas, domínios e FKs.

## Regras obrigatórias

Conferir a licença da republicação utilizada e registrar falhas de acesso.
Separar evidência observada de proposta.
Inspecionar todos os registros, sem inferir qualidade de uma amostra.
Preservar os bytes dos CSVs extraídos; registrar versão e SHA-256 do ZIP.
Usar Python 3.13 se a resolução e importação das dependências funcionarem.

## Comportamentos proibidos

Implementar ingestão, transformação, marts ou dashboard; criar pizza.duckdb;
inventar resultados, licença, cobertura ou commits; publicar dados ou projeto;
copiar indicadores ou filtros de outros projetos sem respaldo nos dados da pizzaria.

## Tratamento de erros

Fonte inacessível ou licença não demonstrada vira pendência explícita. CSV
ausente, encoding não declarado ou formato inesperado interrompe a inspeção.
Não substituir dados reais por sintéticos. Não deduzir nulos sem explicar a
convenção CSV: campo vazio é contado como vazio, não como NULL SQL já ingerido.

## Critérios de aceite mensuráveis

1. Metodologia de desenvolvimento documentada com aplicação ao projeto.
2. Fonte exata e licença evidenciadas, com consulta datada.
3. Quatro CSVs inventariados com colunas, contagens e SHA-256.
4. Quatro grãos e três relacionamentos PK/FK documentados.
5. Onze candidatos analíticos com limites e critérios de validação, incluindo
   rankings por variante e consolidado por tipo.
6. Ambiente instalado e importações verificadas em Python 3.13.
7. Zero módulos de pipeline, zero SQL de marts, zero banco criado.
8. Pendências e comandos executados registrados; aprovação ainda pendente.

## Justificativa das decisões

Inspeção com biblioteca padrão evita inferência de tipos e independe do futuro
pipeline. Dados locais ficam ignorados no Git para manter a publicação uma
decisão explícita. Specs futuras são propostas, não decisões aprovadas.
