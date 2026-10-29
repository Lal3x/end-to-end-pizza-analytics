# Interface de notebooks DuckDB

Criados specs/ui.md antes do código e ui.py; README atualizado com comando e
exemplos SELECT. Não há dependência Python adicional nem alteração de indicadores.

Consultada a documentação oficial da versão 1.5:
https://duckdb.org/docs/1.5/core_extensions/ui.html. Ela confirma start_ui(),
start_ui_server(), porta padrão 4213 e necessidade de conexão normal para
armazenar notebooks. A proposta inicial de read_only foi corrigida na spec
antes de executar o script: abrir UI diretamente em banco somente leitura
não é suportado.

Verificações reais:

- Consulta a duckdb_extensions(): ui instalada, inicialmente não carregada.
- LOAD ui e duckdb_functions(): start_ui, start_ui_server e stop_ui_server presentes.
- Ruff encontrou uma linha longa; corrigida por patch. Check e format check
  de ui.py aprovados; `ruff check .` aprovado após implementação.
- `.venv/bin/python ui.py --no-browser`: servidor iniciou em localhost:4213.
  Execução inicial no sandbox ficou inacessível de fora; encerrada com SIGINT,
  retornando saída zero e “Interface encerrada”, sem traceback.
- Nova execução autorizada fora do sandbox, com --no-browser: curl retornou
  HTTP 200. Ctrl+C encerrou com saída zero e sem traceback.
- Após encerramento, conexão normal ao banco foi reaberta e count de raw.orders
  retornou 21.350, confirmando liberação do arquivo.
- Cópia do script em diretório temporário sem banco, executada por subprocess:
  saída 1, orientação para ingestão e nenhum pizza.duckdb criado.

A validação HTTP confirma o servidor, não interação visual: o navegador não
foi aberto nesta verificação e nenhum notebook foi criado por automação.
O modo padrão usa start_ui para abrir o navegador do usuário. Nenhuma etapa
de transformação foi executada e nenhum servidor de teste ficou em execução.
ui.py está fora da medição de cobertura conforme a configuração do projeto;
não foi adicionada dependência de extensão/rede aos testes unitários.
