"""Notebooks SQL locais, conforme specs/ui.md; não executa o pipeline."""

import argparse
import sys
import threading
from pathlib import Path

import duckdb


def main() -> int:
    """Abre somente banco existente e mantém o servidor até Ctrl+C."""
    parser = argparse.ArgumentParser(description="Notebooks locais do DuckDB")
    parser.add_argument("--no-browser", action="store_true", help="Não abrir navegador")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    banco = Path(__file__).resolve().parent / "pizza.duckdb"
    if not banco.is_file():
        print(
            "Banco ausente. Execute: uv run python -m pipeline.ingestao",
            file=sys.stderr,
        )
        return 1
    try:
        with duckdb.connect(str(banco)) as con:
            con.execute("INSTALL ui")
            con.execute("LOAD ui")
            comando = "start_ui_server" if args.no_browser else "start_ui"
            url = con.execute(f"CALL {comando}()").fetchone()[0]
            print(f"DuckDB UI: {url}\nCtrl+C para encerrar.", flush=True)
            threading.Event().wait()
    except KeyboardInterrupt:
        print("\nInterface encerrada.")
        return 0
    except duckdb.Error as erro:
        print(f"Erro ao abrir DuckDB UI: {erro}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
