"""Entrada CLI para aquisição; contrato em specs/ingestao.md."""

import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from pipeline.aquisicao import main

    sys.exit(main())
