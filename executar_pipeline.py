"""Execução atômica das três etapas conforme specs/execucao-pipeline.md.

Fontes pré-validadas antes de abrir o destino; uma conexão e um commit global.
Reutiliza regras existentes, preserva outros schemas e nunca inicia interfaces.
Somente anuncia sucesso depois de publicar todas as camadas. Não baixa fontes.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import duckdb

from pipeline import ingestao, marts, transformacao

RAIZ = Path(__file__).resolve().parent


def executar_pipeline(banco: Path | None = None) -> dict:
    """Publica RAW/refined/marts em uma transação, preservando a versão anterior.

    Args:
        banco: Destino de ensaio ou padrão pizza.duckdb junto ao módulo.

    Returns:
        Estado publicado, diagnósticos por etapa e duração total após commit.

    Raises:
        RuntimeError: Se qualquer etapa falhar; informa etapa e causa original.
        KeyboardInterrupt: Após rollback/fechamento se o usuário interromper.

    Não suporta execuções concorrentes. Limpa destino novo somente quando sua
    criação foi confirmada e a identidade do arquivo não mudou. Não apaga banco
    preexistente nem schemas externos. Conexão sempre fechada, inclusive em erro.
    """
    destino = (Path(banco) if banco is not None else RAIZ / "pizza.duckdb").resolve()
    inicio = time.perf_counter()
    etapa = "pré-validação"
    criado = None
    publicado = False
    try:
        ingestao.validar_fontes()
        etapa = "conexão"
        destino.parent.mkdir(parents=True, exist_ok=True)
        existia = destino.exists()
        with duckdb.connect(":memory:") as con:
            literal = str(destino).replace("'", "''")
            con.execute(f"ATTACH '{literal}' AS destino")
            if not existia:
                stat = destino.stat()
                criado = (stat.st_dev, stat.st_ino)
            con.execute("USE destino")
            con.execute("SET TimeZone='UTC'")
            con.execute("BEGIN")
            try:
                etapa = "ingestao"
                con.execute("DROP SCHEMA IF EXISTS marts CASCADE")
                con.execute("DROP SCHEMA IF EXISTS refined CASCADE")
                relatorio = {"ingestao": ingestao.executar(con=con)}
                etapa = "transformacao"
                relatorio[etapa] = transformacao.executar(con=con)
                etapa = "marts"
                relatorio[etapa] = marts.executar(con=con)
                etapa = "commit"
                con.execute("COMMIT")
                publicado = True
            except BaseException:
                con.execute("ROLLBACK")
                raise
        return {
            "estado": "publicado",
            "etapas": relatorio,
            "segundos": round(time.perf_counter() - inicio, 3),
        }
    except BaseException as erro:
        if criado is not None and not publicado and destino.exists():
            stat = destino.stat()
            if (stat.st_dev, stat.st_ino) == criado:
                destino.unlink()
        if isinstance(erro, Exception):
            raise RuntimeError(f"Falha na etapa {etapa}: {erro}") from erro
        raise


def main() -> int:
    """CLI UTF-8: sucesso após commit, erro com status 1 e Ctrl+C com 130."""
    parser = argparse.ArgumentParser(description="Pipeline completo Pizza Paradise")
    parser.add_argument("--banco", type=Path, help="Destino de ensaio")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        print(json.dumps(executar_pipeline(args.banco), ensure_ascii=False, indent=2))
    except KeyboardInterrupt:
        print("Pipeline interrompido; transação revertida.", file=sys.stderr)
        return 130
    except Exception as erro:
        print(f"Erro no pipeline completo: {erro}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
