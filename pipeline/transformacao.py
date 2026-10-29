"""Transformação pandas conforme specs/transformacao.md.

Lê uma tabela RAW por vez, valida e converte explicitamente no DataFrame.
SQL somente lê, persiste tipos e audita relações/reconciliações no destino.
Publica refined em transação única; qualquer falha restaura a versão anterior.
"""

import argparse
import json
import math
import resource
import sys
import time
from decimal import Decimal
from pathlib import Path

import duckdb
import pandas as pd

import db
from pipeline.ingestao import FONTES

CHAVES = {"orders": "id", "products": "SKU", "customers": "id", "stores": "id"}
TEXTOS = {
    "orders": ["id", "customerId", "storeId", "orderDate"],
    "order_items": ["SKU", "orderID"],
    "products": ["SKU", "Name", "Category", "Size", "Ingredients"],
    "customers": ["id"],
    "stores": ["id", "zipcode", "state_abbr", "city", "state"],
}


def exigir(condicao: pd.Series, contexto: str, valores: pd.Series) -> None:
    """Falha com contexto e exemplos quando alguma linha viola uma regra."""
    invalidos = ~condicao.fillna(False)
    if invalidos.any():
        exemplos = valores.loc[invalidos].head(3).astype(str).tolist()
        raise ValueError(f"{contexto}: {int(invalidos.sum())} inválidos; {exemplos}")


def dinheiro(serie: pd.Series, contexto: str, binario: bool = False) -> pd.Series:
    """Converte para Decimal sem aceitar centavos extras ou números não finitos.

    Args:
        serie: Valores obrigatórios, textuais ou DOUBLE conforme a origem.
        contexto: Tabela e coluna usadas no diagnóstico de erros.
        binario: Permite somente ruído DOUBLE de até 1e-9 na quantização.

    Raises:
        ValueError: Se o valor não couber em DECIMAL(18,2) ou violar o contrato.
    """
    if not binario:
        exigir(
            serie.astype("string").str.fullmatch(r"[0-9]+([.][0-9]{1,2})?"),
            contexto,
            serie,
        )

    def converter(valor):
        """Valida uma representação e devolve exatamente duas casas decimais."""
        try:
            numero = Decimal(str(valor))
            if not numero.is_finite() or numero < 0 or numero >= Decimal(10**16):
                raise ValueError("fora do domínio DECIMAL(18,2)")
            centavos = numero.quantize(Decimal("0.01"))
            if centavos >= Decimal(10**16):
                raise ValueError("arredondamento excede DECIMAL(18,2)")
            if binario and abs(float(valor) - float(centavos)) > 1e-9:
                raise ValueError("diferença acima de 1e-9")
            return centavos
        except (ArithmeticError, ValueError) as erro:
            raise ValueError(f"{contexto}: valor {valor!r}: {erro}") from erro

    return serie.map(converter)


def transformar(nome: str, quadro: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Valida e transforma uma tabela em pandas sem modificar o quadro recebido.

    Returns:
        DataFrame pronto para persistir e diagnóstico de tipos, nulos,
        duplicatas, formatos temporais e correções aplicadas.

    Raises:
        ValueError: Se houver nulos obrigatórios, conflitos ou domínio inválido.
    """
    if list(quadro.columns) != FONTES[nome]["colunas"] or quadro.empty:
        raise ValueError(f"raw.{nome}: colunas divergentes ou tabela vazia")
    relatorio = {
        "antes": len(quadro),
        "tipos_antes": quadro.dtypes.astype(str).to_dict(),
        "nulos_antes": quadro.isna().sum().astype(int).to_dict(),
        "exemplos_antes": quadro.head(2).astype(str).to_dict("records"),
    }
    df = quadro.copy()
    for coluna in df:
        if coluna != "Ingredients":
            exigir(df[coluna].notna(), f"{nome}.{coluna}: nulos", df[coluna])
    for coluna in TEXTOS[nome]:
        df[coluna] = df[coluna].astype("string")
        if coluna != "Ingredients":
            exigir(df[coluna].str.strip().ne(""), f"{nome}.{coluna}: vazio", df[coluna])

    # Detectar conflitos antes das conversões impede esconder diferenças da fonte.
    repetidas = int(df.duplicated().sum())
    if nome in CHAVES:
        df = df.drop_duplicates().copy()
        chave = CHAVES[nome]
        exigir(~df[chave].duplicated(False), f"{nome}.{chave}: conflito", df[chave])
    relatorio["duplicatas_removidas"] = repetidas if nome in CHAVES else 0
    relatorio["repeticoes_preservadas"] = repetidas if nome == "order_items" else 0

    if nome == "orders":
        itens = pd.to_numeric(df["nItems"], errors="raise")
        exigir(
            itens.map(math.isfinite)
            & itens.gt(0)
            & itens.mod(1).eq(0)
            & itens.le(2**31 - 1),
            "orders.nItems",
            df["nItems"],
        )
        df["nItems"] = itens.astype("int32")
        df["total"] = dinheiro(df["total"], "orders.total", binario=True)
        origem = df["orderDate"]
        df["order_timestamp"] = pd.Series(
            pd.NaT, index=df.index, dtype="datetime64[ns, UTC]"
        )
        df["order_date"] = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
        df["timestamp_precision"] = pd.Series(pd.NA, index=df.index, dtype="string")
        for precisao, regex, formato in (
            ("second", r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", "%Y-%m-%dT%H:%M:%SZ"),
            ("minute", r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z", "%Y-%m-%dT%H:%MZ"),
            ("date", r"\d{4}-\d{2}-\d{2}", "%Y-%m-%d"),
        ):
            mascara = origem.str.fullmatch(regex)
            datas = pd.to_datetime(
                origem[mascara], format=formato, errors="raise", utc=True
            )
            df.loc[mascara, "order_date"] = datas.dt.tz_localize(None).dt.normalize()
            if precisao != "date":
                df.loc[mascara, "order_timestamp"] = datas
            df.loc[mascara, "timestamp_precision"] = precisao
        exigir(df["timestamp_precision"].notna(), "orders.orderDate: formato", origem)
        df["order_date"] = df["order_date"].dt.date
        relatorio["precisoes"] = df["timestamp_precision"].value_counts().to_dict()
    elif nome == "products":
        df["Price"] = dinheiro(df["Price"], "products.Price")
        for coluna, dominio in (
            ("Size", {"Small", "Medium", "Large", "Extra Large"}),
            ("Category", {"Classic", "Vegetarian", "Specialty"}),
        ):
            exigir(
                df[coluna].isin(dominio), f"products.{coluna}: domínio novo", df[coluna]
            )
        origem = df["Launch"].astype("string")
        corrigir = origem.str.fullmatch(r"\d{4}-\d{2}-\d{2},")
        exigir(
            ~corrigir | (df["SKU"].isin(["PZ026", "PZ027"]) & origem.eq("2020-01-01,")),
            "products.Launch: correção não prevista",
            origem,
        )
        corrigida = origem.mask(corrigir, origem.str.removesuffix(","))
        relatorio["correcoes_launch"] = [
            {
                "SKU": df.at[i, "SKU"],
                "original": origem.at[i],
                "corrigido": corrigida.at[i],
            }
            for i in df.index[corrigir]
        ]
        exigir(corrigida.str.fullmatch(r"\d{4}-\d{2}-\d{2}"), "products.Launch", origem)
        df["Launch"] = pd.to_datetime(
            corrigida, format="%Y-%m-%d", errors="raise"
        ).dt.date
    elif nome in {"customers", "stores"}:
        for coluna in ["latitude", "longitude"] + (
            ["distance"] if nome == "stores" else []
        ):
            valores = pd.to_numeric(df[coluna], errors="raise").astype("float64")
            validos = valores.map(math.isfinite)
            if coluna != "distance":
                limite = 90 if coluna == "latitude" else 180
                validos &= valores.between(-limite, limite)
            exigir(validos, f"{nome}.{coluna}", df[coluna])
            df[coluna] = valores
    relatorio["depois"] = len(df)
    relatorio["tipos_pandas"] = df.dtypes.astype(str).to_dict()
    relatorio["nulos_depois"] = df.isna().sum().astype(int).to_dict()
    relatorio["exemplos_depois"] = df.head(2).astype(str).to_dict("records")
    return df, relatorio


def validar_relacoes(con: duckdb.DuckDBPyConnection) -> dict:
    """Audita quatro FKs e reconcilia itens/centavos por pedido no destino.

    SQL de auditoria independente das conversões pandas; falhas impedem commit.
    """
    relatorio = {}
    for filha, fk, pai, pk in (
        ("orders", "customerId", "customers", "id"),
        ("orders", "storeId", "stores", "id"),
        ("order_items", "orderID", "orders", "id"),
        ("order_items", "SKU", "products", "SKU"),
    ):
        chave = f"{filha}.{fk}->{pai}.{pk}"
        relatorio[chave] = con.execute(
            f"SELECT count(*) FROM refined.{filha} f ANTI JOIN refined.{pai} p "
            f"ON f.{fk}=p.{pk}"
        ).fetchone()[0]
        if relatorio[chave]:
            raise ValueError(f"FK {chave}: {relatorio[chave]} órfãos")
    divergentes = con.execute(
        "WITH itens AS (SELECT i.orderID, count(*) AS n, sum(p.Price) AS total "
        "FROM refined.order_items i JOIN refined.products p USING (SKU) "
        "GROUP BY i.orderID) "
        "SELECT o.id FROM refined.orders o LEFT JOIN itens i ON o.id=i.orderID "
        "WHERE i.n IS NULL OR i.n<>o.nItems OR i.total<>o.total LIMIT 3"
    ).fetchall()
    if divergentes:
        raise ValueError(f"Reconciliação nItems/total: pedidos {divergentes}")
    relatorio["pedidos_divergentes"] = 0
    return relatorio


def executar(banco: Path | None = None) -> dict:
    """Recria refined atomicamente e retorna diagnósticos após o commit.

    Args:
        banco: Banco existente para ensaio; padrão pizza.duckdb na raiz.

    Raises:
        ValueError: Se conversões ou auditorias violarem o contrato.
        duckdb.Error: Se a leitura, persistência ou transação falhar.

    RAW permanece intacta; qualquer erro restaura refined anterior.
    """
    caminho = Path(banco) if banco is not None else db.PASTA_RAW.parent / "pizza.duckdb"
    if not caminho.is_file():
        raise ValueError(f"Banco ausente: {caminho}; execute a ingestão")
    inicio = time.perf_counter()
    relatorio = {"tabelas": {}}
    with duckdb.connect(str(caminho)) as con:
        con.execute("SET TimeZone='UTC'")
        con.execute("BEGIN")
        try:
            con.execute("DROP SCHEMA IF EXISTS refined CASCADE")
            db.criar_schema(con, "refined")
            for nome in FONTES:
                quadro = con.execute(f"SELECT * FROM raw.{nome}").df()
                try:
                    df, diagnostico = transformar(nome, quadro)
                except (ValueError, TypeError, ArithmeticError) as erro:
                    raise ValueError(f"raw.{nome}: {erro}") from erro
                del quadro
                monetaria = {"orders": "total", "products": "Price"}.get(nome)
                # DuckDB amostra object/Decimal e pode inferir precisão insuficiente.
                # Transporte textual exato; o tipo definitivo é declarado abaixo,
                # ainda na mesma transação. Nenhum valor passa por float aqui.
                if monetaria:
                    df[monetaria] = df[monetaria].map(str).astype("string")
                gravadas = db.gravar(con, df, "refined", nome)
                # Tipos físicos explícitos; nenhuma regra de negócio é feita em SQL.
                if monetaria:
                    con.execute(
                        f'ALTER TABLE refined.{nome} ALTER "{monetaria}" '
                        "TYPE DECIMAL(18,2)"
                    )
                tipos = {
                    r[0]: r[1]
                    for r in con.execute(f"DESCRIBE refined.{nome}").fetchall()
                }
                if monetaria and tipos[monetaria] != "DECIMAL(18,2)":
                    raise ValueError(f"refined.{nome}: tipo monetário incorreto")
                if gravadas != len(df):
                    raise ValueError(f"refined.{nome}: contagem divergente")
                diagnostico["tipos_destino"] = tipos
                diagnostico["linhas_destino"] = gravadas
                relatorio["tabelas"][nome] = diagnostico
                del df
            relatorio["validacoes"] = validar_relacoes(con)
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
    relatorio["segundos"] = round(time.perf_counter() - inicio, 3)
    relatorio["pico_rss_mib"] = round(
        resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 2
    )
    return relatorio


def main() -> int:
    """Executa a etapa e imprime JSON UTF-8; em erro retorna status 1."""
    parser = argparse.ArgumentParser(description="Transformação pandas Pizza Paradise")
    parser.add_argument("--banco", type=Path, help="Banco existente para ensaio")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        print(json.dumps(executar(args.banco), ensure_ascii=False, indent=2))
    except Exception as erro:
        print(f"Erro na transformação: {erro}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
