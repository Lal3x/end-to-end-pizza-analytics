"""Impede versionar artefatos locais, conforme specs/automacao-documentacao.md."""

import sys
from pathlib import PurePosixPath


def proibidos(arquivos: list[str]) -> list[str]:
    """Identifica fontes/bancos/caches/credenciais pelo caminho, sem lê-los."""
    erros = []
    for nome in arquivos:
        caminho = PurePosixPath(nome)
        partes = caminho.parts
        if (
            partes[0] in {"raw", "data", "site", ".venv", ".venv-validacao"}
            or "AGENTS.md" in partes
            or caminho.suffix.lower() in {".duckdb", ".parquet", ".wal"}
            or (caminho.name.startswith(".env") and caminho.name != ".env.example")
        ):
            erros.append(nome)
    return erros


if __name__ == "__main__":
    falhas = proibidos(sys.argv[1:])
    if falhas:
        print("Arquivos locais não podem ser publicados:\n" + "\n".join(falhas))
    sys.exit(1 if falhas else 0)
