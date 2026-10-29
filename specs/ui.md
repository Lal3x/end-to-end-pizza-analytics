# Interface local de notebooks DuckDB

Status: solicitada como ferramenta de exploração após a ingestão.

## CONTEXTO

Permitir explorar pizza.duckdb com notebooks SQL no navegador, sem misturar
interface e ingestão. Esta spec precede ui.py.

## STACK

Python 3.13, uv, DuckDB e sua extensão oficial ui; sem nova biblioteca Python.

## O QUE JÁ EXISTE

Banco pizza.duckdb com cinco tabelas raw Pizza Paradise; db.py na raiz. A extensão
ui está instalada no ambiente atual, mas deve ser instalada se faltar em outra
máquina. Instalação inicial e recursos visuais podem precisar de rede.

## ARTEFATO A PRODUZIR

ui.py, executável com `uv run python ui.py`.

## SPEC

### U1. ABERTURA E BANCO AUSENTE

Resolver pizza.duckdb pela localização de ui.py. Se não existir, orientar
   ingestão e sair com código 1, sem criar banco. Não usar conectar(), pois cria
   arquivo ausente. Motivo: banco vazio não pode parecer carga incompleta.
### U2. EXTENSÃO E CONEXÃO

Abrir conexão normal, instalar/carregar ui e chamar start_ui(). A UI usa
   tabelas internas para armazenar notebooks e não suporta abrir diretamente
   o banco em modo somente leitura. Não executar mudanças em raw/refined/marts
   no inicializador. Motivo: suportar os notebooks nativos sem misturar etapas.
### U3. ATÉ CTRL+C

Imprimir a URL e manter o processo ativo até Ctrl+C; fechar conexão ao sair,
   sem traceback de interrupção. Motivo: servidor depende da conexão viva.
### U4. MODO SEM NAVEGADOR

Oferecer --no-browser, usando start_ui_server(), para abrir a URL manualmente
   e validar o servidor sem lançar aplicativo gráfico.
### U5. SEPARAÇÃO

Não importar ingestao nem executá-la. Não criar tabelas ou indicadores.
   Antes de rodar etapas que escrevem, encerrar ui.py: leitura aberta em outro
   processo pode impedir escrita no arquivo.
### U6. SAÍDA E ERRO

Erro de extensão, porta ou conexão deve imprimir causa e saída 1. stdout
   em UTF-8. Não iniciar servidor ao importar o módulo.

## CRITÉRIOS DE ACEITE

- Banco ausente: erro com comando de ingestão e nenhum arquivo novo.
- --no-browser serve resposta HTTP na URL anunciada e expõe o banco existente.
- Ctrl+C encerra sem traceback; banco pode ser reaberto após a saída.
- Ruff aprovado; validação HTTP não substitui conferência visual no navegador.

## ENTREGA

Script, instruções no README e registro dos comandos/resultados efetivamente
executados. Nenhuma execução de transformação integra esta ferramenta.
