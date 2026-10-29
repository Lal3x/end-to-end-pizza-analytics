# Validação da automação e entrega

## Escopo e decisões — 29/10/2026

Implementação conforme [spec](../specs/automacao-documentacao.md): pre-commit,
CI com testes e cobertura, documentação MkDocs e deploy do site pelo Pages após
aprovação dos checks na main. O Pages hospeda a documentação; o dashboard
Streamlit continua sendo executado separadamente.

O usuário escolheu preparar tudo para publicação posterior. Não houve push,
merge, ativação do Pages ou execução remota de GitHub Actions nesta etapa.
Os passos restantes estão no [guia de automação](automacao.md).

## Verificações executadas

Foi criada uma cópia dos arquivos candidatos, sem banco, fontes originais ou
ambiente virtual. Um novo ambiente Python 3.13.14 foi instalado com
`uv sync --locked --group docs`, usando uv 0.12.24 e reutilizando seu cache.

| Verificação | Resultado |
| --- | --- |
| `pytest --cov` no ambiente novo | 127 aprovados em 22,51 s; cobertura 94,81% |
| Pre-commit em todos os arquivos | Aprovado |
| Arquivo .env artificial adicionado à força na cópia | Bloqueado pelo hook |
| `mkdocs build --strict` | Aprovado |
| Nova aquisição dos cinco anexos | Hashes conferidos |
| Pipeline completo na cópia, com banco novo | 38,891 s; pico RSS 1.804,41 MiB |
| Comparação das 23 tabelas com a execução anterior | Tipos iguais; zero diferenças nos dois sentidos por EXCEPT ALL |

Os testes sintéticos passaram antes de baixar os dados e sem criar o banco do
projeto. A reprodução com a fonte real foi uma verificação separada. Tempos e
memória são medições desta máquina, sem garantia para outros ambientes.

[Registro estruturado](evidencias/automacao-validacao.json).
[Prévia local da documentação](evidencias/documentacao-preview.png).

## Organização e limites

O site separa início, execução, dados e indicadores, operação, entrega e histórico.
Os relatórios históricos foram preservados no repositório. Na revisão editorial
posterior, passaram a ser excluídos do site e do índice de busca.
Links para código e specs apontam para o repositório; banco e anexos completos
não entram no site. A política da fonte foi reconferida sem atribuir uma licença
padronizada ausente nos metadados.

As ações do workflow foram fixadas por SHA e seus identificadores conferidos
na API pública do GitHub. O deploy depende de checks aprovados e só ocorre na
main, com permissões de escrita de Pages restritas ao job de publicação.
A execução no GitHub ainda precisa ser conferida depois do envio autorizado.

Os commits locais registram primeiro ferramentas, depois o executor anteriormente
pendente e finalmente automação/documentação. As datas e o histórico anteriores
foram preservados. AGENTS.md, fontes, banco, backups e ambientes ficam ignorados.
