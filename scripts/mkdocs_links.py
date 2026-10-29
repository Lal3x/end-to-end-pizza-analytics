"""Resolve links fora de docs/ sem publicar a árvore do projeto no Pages.

Contrato em specs/automacao-documentacao.md. Apenas arquivos existentes dentro
do repositório podem virar links públicos; URLs e âncoras permanecem intactas.
"""

import re
from pathlib import Path
from urllib.parse import quote, urlsplit

RAIZ = Path(__file__).resolve().parents[1]
DOCS = RAIZ / "docs"
REPO = "https://github.com/Lal3x/end-to-end-pizza-analytics"


def on_page_markdown(markdown, page, config, files):
    """Aponta código/specs ao GitHub e imagens externas a docs/ ao raw do repo."""

    def substituir(match):
        inicio, alvo, fim = match.groups()
        url = urlsplit(alvo)
        if url.scheme or url.netloc or not url.path or alvo.startswith("#"):
            return match.group(0)
        caminho = (DOCS / page.file.src_uri).parent / url.path
        caminho = caminho.resolve()
        if not caminho.is_file() or not caminho.is_relative_to(RAIZ):
            return match.group(0)
        if caminho.is_relative_to(DOCS):
            return match.group(0)
        relativo = quote(caminho.relative_to(RAIZ).as_posix(), safe="/")
        if inicio.startswith("!"):
            destino = (
                "https://raw.githubusercontent.com/Lal3x/end-to-end-pizza-analytics/main/"
                + relativo
            )
        else:
            destino = f"{REPO}/blob/main/{relativo}"
        if url.fragment:
            destino += "#" + url.fragment
        return inicio + destino + fim

    return re.sub(r"(!?\[[^\]]*\]\()([^\s)]+)(\))", substituir, markdown)
