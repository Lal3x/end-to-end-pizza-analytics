# Execução completa do pipeline Pizza Paradise

Status: implementado e validado em 29/10/2026, após autorização e destaque dos
cuidados de transação, compatibilidade dos comandos e recarga do dashboard.
Resultados medidos em docs/execucao-pipeline.md.

## CONTEXTO

Executar ingestão → transformação pandas → marts por um comando, reutilizando
as etapas existentes e preservando uma versão completa em caso de falha.
Hoje cada etapa abre sua conexão/transação, e a ingestão recusa refined/marts
existentes. Portanto, somente chamar executar() três vezes não resolve a
reexecução nem oferece rollback do conjunto.

## STACK

Python 3.13, uv e DuckDB local; pandas permanece na transformação.
Sem orquestrador, processo agendado, banco auxiliar ou dependência nova.

## O QUE JÁ EXISTE (use, não reimplemente)

- db.py na raiz, conexão e persistência compartilhadas.
- pipeline/ingestao.py, pipeline/transformacao.py e pipeline/marts.py, cada um
  com executar(banco=None), CLI própria, testes e transação individual.
- Cinco fontes em raw/pizza_paradise/ e baixar_dados.py independente.
- SQLs de marts e auditorias de refined/marts já validados.
- Dashboard separado, com cache de dados e leitura somente de marts.

## ARTEFATOS A PRODUZIR

1. executar_pipeline.py, na raiz, com executar_pipeline(banco=None) -> dict.
2. Refatoração mínima nas funções das três etapas para aceitar uma conexão
   externa sem abrir/confirmar/fechar a transação do chamador.
3. test/test_execucao_pipeline.py, atualização dos testes de cada etapa,
   README e registro de execução real em docs/execucao-pipeline.md.

Comandos implementados e validados:

```bash
uv run python executar_pipeline.py
uv run python executar_pipeline.py --banco caminho/ensaio.duckdb
```

Não criar outro módulo em pipeline/, placeholders ou cópias das regras de negócio.

## SPEC

### 1. ESCOPO E ORDEM

Executar exatamente ingestão, transformação e marts, nessa ordem e no mesmo
banco. Transformações continuam no pandas; indicadores continuam nos SQLs.
Reutilizar funções Python, sem chamar CLIs por subprocess ou interpretar stdout.
Motivo: manter erros, dados e transação sob um controle explícito.

O executor não baixa fontes, abre UI, inicia Streamlit ou gera rascunhos.
Aquisição continua explícita por baixar_dados.py antes da primeira execução.
Motivo: execução local reproduzível sem rede obrigatória ou processos extras.

### 2. PRÉ-VALIDAÇÃO E CAMINHOS

Resolver o banco padrão pela raiz do módulo, nunca pelo diretório corrente.
Um caminho relativo fornecido explicitamente em --banco segue o diretório
corrente, como nas CLIs individuais; caminho absoluto é usado como informado.
--banco permite criar um banco de ensaio ou atualizar um existente.
Antes de abrir/criar o destino, validar as cinco fontes usando a lógica da
ingestão. Extrair essa pré-validação para função na própria ingestao.py e
reutilizá-la, sem copiar cabeçalhos/tipos/regras para o executor.
Motivo: fonte ausente/inválida não pode criar banco vazio nem iniciar a carga.

### 3. UMA CONEXÃO E UMA TRANSAÇÃO

Após pré-validar, abrir uma conexão, iniciar BEGIN e executar todas as etapas
com essa conexão. Dentro da transação, remover marts e refined antes da
ingestão. Ela então recria RAW conforme seu contrato; as demais etapas recriam
refined e marts. COMMIT somente após concluir todas as auditorias.
Motivo: impedir RAW nova com refined/marts antigos e permitir reexecução completa.
Essa é a conexão compartilhada de destino. Pré-validações Parquet podem usar
conexão em memória separada, sem abrir/escrever o arquivo de destino. A ingestão
revalida as fontes ao entrar na etapa usando a mesma função, sem duplicar regras.

Não remover o arquivo pizza.duckdb, trocar por banco novo, copiar/sobrescrever
o destino ou apagar schemas não pertencentes às etapas. Tabelas internas de
notebooks e outros schemas permanecem. Motivo: preservar exploração e conteúdo
que não pertence à execução do pipeline.

### 4. CONTRATO DAS ETAPAS

Estender executar(banco=None, *, con=None) nas três etapas:

- Sem con: comportamento atual, conexão própria, transação própria e fechamento.
- Com con: usar a conexão recebida; não iniciar transação, executar COMMIT,
  ROLLBACK ou fechar conexão. Propagar falhas ao chamador.
- banco e con fornecidos juntos: ValueError, sem escrever dados.

O chamador garante uma transação ativa ao fornecer con. O executor não captura
erros para continuar com etapas seguintes. As validações e retornos das etapas
são preservados. Não alterar suas regras monetárias, temporais ou de grão.

A ingestão isolada continua bloqueando refined/marts existentes. Não adicionar
uma opção genérica de força para contornar essa proteção. A execução completa
remove as camadas derivadas dentro da transação compartilhada; rollback as restaura.
Motivo: segurança de reexecução sem enfraquecer os comandos individuais.

### 5. FALHA E REEXECUÇÃO

Falha de fonte: parar antes da abertura do banco. Falha após BEGIN, inclusive
auditoria financeira/FK ou mart vazio: ROLLBACK do conjunto, indicar etapa e
causa, retornar status 1 e fechar a conexão. Não imprimir sucesso parcial.
Se já havia banco válido, suas três camadas e schemas externos permanecem.
Em destino novo, não deixar tabelas parcialmente publicadas; remover o arquivo
vazio criado por esta execução somente após fechar e confirmar que não existia
antes. Nunca remover arquivo preexistente.

Executar duas vezes com as mesmas fontes mantém valores, tipos e multiplicidades.
Não incluir retomada automática por etapa, retries ou execução concorrente.
Motivo: a unidade de publicação deste comando é o pipeline inteiro.
Ctrl+C provoca rollback/fechamento e saída 130. A garantia cobre falhas tratáveis
durante a execução, não substitui backup contra falha de disco/energia. Remover
destino novo apenas quando sua criação foi confirmada e sua identidade de arquivo
não mudou; nunca apagar um arquivo que apareceu/trocou de lugar por outro processo.

### 6. SAÍDA E OPERAÇÃO

Após COMMIT, retornar/imprimir relatório UTF-8 com ordem/estado das três etapas,
contagens por camada/tabela e duração. Retornos de etapas são diagnósticos
internos até o commit global, não três publicações independentes.
Não somar linhas de grãos/camadas diferentes como se fossem pedidos ou vendas.

Conexão sempre fechada. UI DuckDB deve estar encerrada; bloqueio por outro
processo gera erro claro, sem encerrar processos do usuário. O Streamlit pode
continuar aberto entre leituras; não conserva conexão. Leitura simultânea no
instante da carga pode causar conflito e deve falhar claramente, sem retries.
Depois de publicar, clicar em Recarregar dados no painel: o executor não limpa
o cache de outro processo nem promete atualização automática da tela.

## CRITÉRIOS DE ACEITE

1. Fontes sintéticas válidas geram cinco RAW, cinco refined e 13 marts no
   mesmo banco por uma única chamada; os totais reconciliam.
2. Reexecução compara valores/tipos/multiplicidades, não só contagens.
3. Fonte ausente/inválida não cria banco nem modifica um existente.
4. Erro real de conversão após ingestão restaura as três camadas anteriores.
5. Erro SQL ou reconciliação na etapa marts restaura também RAW/refined anteriores.
6. Schema externo com tabela sentinela permanece em sucesso e falha.
7. Falha em destino novo não deixa arquivo parcial; nunca apagar destino existente.
8. As CLIs individuais mantêm seus comportamentos e o bloqueio da ingestão isolada.
9. Nenhum cálculo de indicador no executor e nenhuma conexão aberta após retorno.
10. Suíte com DuckDB temporário real e fontes sintéticas, sem banco do projeto,
    rede, mocks do DuckDB ou valores esperados copiados da base real.

## ENTREGA

1. Aprovar este contrato antes da implementação, especialmente a transação
   compartilhada e a pequena refatoração das etapas existentes.
2. Docstrings com regras/motivos, implementação e testes de falhas reais.
3. Executar primeiro em banco de ensaio; registrar resultados, duração, cobertura,
   limites e suposições não previstas. Atualizar README com o comando só depois
   de implementá-lo e validá-lo.
4. Preparar commit real da entrega, sem alterar histórico ou publicar externamente.
