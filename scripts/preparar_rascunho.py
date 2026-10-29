"""Atualiza o retrato do protótipo conforme specs/dashboard.md.

Somente SELECT em marts com conexão read_only fechada após a leitura. Valores
financeiros Decimal são serializados como texto exato; nenhuma fórmula nova.
Não requer navegador nem modifica banco, pipeline ou dependências do projeto.
"""

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parents[1]
MARTS = (
    "kpis",
    "vendas_mensais",
    "ranking_tipos_pizza",
    "concentracao_pizzas",
    "pedidos_dia_semana",
    "pedidos_hora",
    "receita_categoria",
    "vendas_loja",
    "frequencia_clientes",
)


def preparar(banco: Path, destino: Path) -> dict:
    """Exporta marts agregados e metadados, falhando em fonte ausente/vazia.

    Args:
        banco: Arquivo DuckDB existente, aberto somente para leitura.
        destino: Diretório que receberá dados.js e dados-metadados.json.

    Returns:
        Metadados de origem, contagens, instante UTC e hash do snapshot.

    Raises:
        ValueError: Se faltar o banco ou um mart estiver vazio.
        duckdb.Error: Se a leitura das tabelas falhar.
    """
    if not banco.is_file():
        raise ValueError(f"Banco ausente: {banco}")
    dados = {}
    with duckdb.connect(str(banco), read_only=True) as con:
        con.execute("BEGIN")
        for nome in MARTS:
            cursor = con.execute(f"SELECT * FROM marts.{nome}")
            colunas = [c[0] for c in cursor.description]
            linhas = cursor.fetchall()
            if not linhas:
                raise ValueError(f"Mart vazio: {nome}")
            dados[nome] = [dict(zip(colunas, linha, strict=True)) for linha in linhas]
        con.execute("COMMIT")
    # Ordenação de apresentação, sem agregações ou cálculos de indicadores.
    dados["vendas_mensais"].sort(key=lambda r: r["mes"])
    dados["ranking_tipos_pizza"].sort(key=lambda r: (-r["receita"], r["Name"]))
    dados["concentracao_pizzas"].sort(key=lambda r: r["ordem"])
    dados["pedidos_dia_semana"].sort(key=lambda r: r["dia_iso"])
    dados["pedidos_hora"].sort(
        key=lambda r: (r["hora_local"] is None, r["hora_local"] or 0)
    )
    dados["receita_categoria"].sort(key=lambda r: (-r["receita"], r["Category"]))
    dados["vendas_loja"].sort(key=lambda r: (-r["receita"], r["storeId"]))
    dados["frequencia_clientes"].sort(key=lambda r: r["frequencia"])
    conteudo = (
        "const DADOS = "
        + json.dumps(dados, ensure_ascii=False, indent=2, default=str, allow_nan=False)
        + ";\n"
    )
    metadados = {
        "gerado_em_utc": datetime.now(UTC).isoformat(),
        "banco": banco.name,
        "somente_leitura": True,
        "tabelas": {f"marts.{nome}": len(linhas) for nome, linhas in dados.items()},
        "dados_js_sha256": hashlib.sha256(conteudo.encode()).hexdigest(),
    }
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "dados.js").write_text(conteudo, encoding="utf-8")
    (destino / "dados-metadados.json").write_text(
        json.dumps(metadados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return metadados


def main() -> None:
    """CLI local para regenerar o retrato a partir dos marts disponíveis."""
    parser = argparse.ArgumentParser(description="Dados reais do rascunho")
    parser.add_argument("--banco", type=Path, default=RAIZ / "pizza.duckdb")
    args = parser.parse_args()
    print(
        json.dumps(preparar(args.banco, RAIZ / "design"), ensure_ascii=False, indent=2)
    )


if __name__ == "__main__":
    main()
