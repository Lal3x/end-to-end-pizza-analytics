"""Confere o Streamlit real no navegador conforme specs/dashboard.md.

Usa marts locais apenas para comparação, não integra a suíte unitária. Com o
servidor já aberto, verifica interações e reexecuta marts para provar ausência
de lock; salva capturas e JSON. Playwright é ferramenta temporária de revisão.
"""

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import duckdb
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parents[1]


def verificar(url: str) -> dict:
    """Compara KPIs/figuras, testa recarga e captura desktop/móvel.

    Args:
        url: Endereço local do Streamlit já iniciado.

    Raises:
        AssertionError: Se números, interações ou layout divergirem.
        subprocess.CalledProcessError: Se reexecutar marts falhar com app aberto.
    """
    with duckdb.connect(str(RAIZ / "pizza.duckdb"), read_only=True) as con:
        valores = con.execute(
            "SELECT receita,pedidos,unidades,ticket_medio FROM marts.kpis"
        ).fetchone()
        nomes = [
            r[0]
            for r in con.execute(
                "SELECT Name FROM marts.concentracao_pizzas ORDER BY ordem"
            ).fetchall()
        ]
        pedidos_inicio = con.execute(
            "SELECT pedidos FROM marts.vendas_mensais ORDER BY mes LIMIT 1"
        ).fetchone()[0]
    esperados = [
        f"{v:,.{2 if i in (0, 3) else 0}f}".replace(",", "_")
        .replace(".", ",")
        .replace("_", ".")
        for i, v in enumerate(valores)
    ]
    destino = RAIZ / "docs/evidencias"
    erros = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": 1440, "height": 1024}, device_scale_factor=1
        )
        page.on("pageerror", lambda e: erros.append(str(e)))
        page.goto(url, wait_until="domcontentloaded")
        page.get_by_role("heading", name="Visão executiva", exact=True).wait_for(
            timeout=30000
        )
        page.wait_for_function(
            "document.querySelectorAll('.js-plotly-plot').length === 7"
        )
        assert page.locator(".cartao .valor").all_text_contents() == esperados
        assert page.locator('[data-testid="stException"]').count() == 0
        for grafico in page.locator('[data-testid="stPlotlyChart"]').all():
            grafico.scroll_into_view_if_needed()
        page.wait_for_function(
            "Array.from(document.querySelectorAll('.js-plotly-plot'))"
            ".every(el => el._fullData)"
        )
        exibidos = page.evaluate(
            "Array.from(document.querySelectorAll('.js-plotly-plot')[2]._fullData[0].x)"
        )
        assert exibidos == nomes

        def escolher(grupo, opcao):
            """Clica no rótulo visível do radio estilizado, como faz o usuário."""
            rotulo = page.get_by_role("radiogroup", name=grupo).get_by_text(
                opcao, exact=True
            )
            rotulo.evaluate("el => el.scrollIntoView({block:'center'})")
            rotulo.click()

        escolher("Série mensal", "Pedidos")
        page.wait_for_function(
            "n => document.querySelector('.js-plotly-plot')._fullData[0].y[0] === n",
            arg=pedidos_inicio,
        )
        assert page.locator(".cartao .valor").all_text_contents() == esperados
        escolher("Ranking", "Variantes (SKU)")
        page.get_by_role(
            "heading", name="02 · Produtos que lideram", exact=True
        ).wait_for()
        # O processo de revisão mantém navegador e servidor de pé durante a escrita.
        carga = subprocess.run(
            [str(RAIZ / ".venv/bin/python"), "-m", "pipeline.marts"],
            cwd=RAIZ,
            check=True,
            capture_output=True,
            text=True,
        )
        page.get_by_role("button", name="Recarregar dados", exact=True).click()
        page.wait_for_function(
            "document.querySelectorAll('.cartao .valor').length === 4"
        )
        assert page.locator(".cartao .valor").all_text_contents() == esperados
        escolher("Série mensal", "Receita")
        escolher("Ranking", "Produtos consolidados")
        page.get_by_role(
            "heading", name="11 · Produtos que lideram", exact=True
        ).wait_for()
        page.wait_for_function(
            "document.querySelectorAll('.js-plotly-plot').length === 7"
        )
        for grafico in page.locator('[data-testid="stPlotlyChart"]').all():
            grafico.scroll_into_view_if_needed()
        assert page.get_by_text("21h tem o maior volume:", exact=False).count() == 1
        assert page.get_by_text("Sem horário informado: 116", exact=False).count() == 1
        page.evaluate("document.querySelector('[data-testid=stMain]').scrollTo(0,0)")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path=str(destino / "dashboard-desktop.png"), full_page=True)
        page.get_by_role(
            "heading", name="O que sustenta a receita", exact=True
        ).evaluate("el=>el.scrollIntoView({block:'start'})")
        page.screenshot(path=str(destino / "dashboard-produtos.png"))
        page.get_by_role(
            "heading", name="Demanda e operação comercial", exact=True
        ).evaluate("el=>el.scrollIntoView({block:'start'})")
        page.screenshot(path=str(destino / "dashboard-demanda.png"))
        page.evaluate("document.querySelector('[data-testid=stMain]').scrollTo(0,0)")
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        assert not page.locator(".cartao .valor").evaluate_all(
            "els=>els.filter(el=>el.scrollWidth>el.clientWidth).map(el=>el.textContent)"
        )
        page.screenshot(path=str(destino / "dashboard-mobile.png"), full_page=True)
        assert not erros, erros
        browser.close()
    relatorio = {
        "url_verificada": url,
        "kpis": esperados,
        "graficos": 7,
        "pareto_nomes": nomes,
        "serie_mensal_e_variantes": "aprovadas",
        "marts_com_streamlit_aberto": json.loads(carga.stdout),
        "recarga_sem_mudanca_de_kpis": True,
        "erros_javascript": erros,
        "viewports": [[1440, 1024], [390, 844]],
        "capturas_sha256": {
            n: hashlib.sha256((destino / n).read_bytes()).hexdigest()
            for n in (
                "dashboard-desktop.png",
                "dashboard-mobile.png",
                "dashboard-produtos.png",
                "dashboard-demanda.png",
            )
        },
    }
    (destino / "dashboard-verificacao.json").write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return relatorio


def main() -> None:
    """Pode iniciar um servidor temporário próprio e sempre encerrá-lo ao sair."""
    parser = argparse.ArgumentParser(description="Verificação visual do dashboard")
    parser.add_argument("--url", default="http://127.0.0.1:8502")
    parser.add_argument("--iniciar-servidor", action="store_true")
    args = parser.parse_args()
    servidor = None
    try:
        if args.iniciar_servidor:
            servidor = subprocess.Popen(
                [
                    str(RAIZ / ".venv/bin/python"),
                    "-m",
                    "streamlit",
                    "run",
                    "app.py",
                    "--server.port",
                    "8502",
                    "--server.address",
                    "127.0.0.1",
                    "--server.fileWatcherType",
                    "none",
                    "--browser.gatherUsageStats",
                    "false",
                ],
                cwd=RAIZ,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )
            for _ in range(60):
                if servidor.poll() is not None:
                    raise RuntimeError("O servidor temporário não iniciou")
                try:
                    with urlopen(args.url + "/_stcore/health", timeout=1) as resposta:
                        if resposta.status == 200:
                            break
                except (URLError, TimeoutError):
                    time.sleep(0.25)
            else:
                raise RuntimeError("Servidor não ficou disponível para verificação")
        print(json.dumps(verificar(args.url), ensure_ascii=False, indent=2))
    finally:
        if servidor is not None:
            servidor.terminate()
            servidor.wait(timeout=10)


if __name__ == "__main__":
    main()
