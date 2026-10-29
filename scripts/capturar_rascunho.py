"""Captura o HTML real e verifica sua apresentação, conforme specs/dashboard.md.

Ferramenta de desenho, fora do pipeline e da suíte unitária. Requer Playwright
temporário e Chromium; não adiciona dependências ao projeto. Compara os KPIs
com SELECTs read_only nos marts e captura somente após a verificação visual.
"""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import duckdb
from playwright.sync_api import sync_playwright
from preparar_rascunho import MARTS

RAIZ = Path(__file__).resolve().parents[1]


def capturar() -> dict:
    """Valida desktop/móvel e salva PNG da página HTML completa a 1440 px.

    Returns:
        Evidências de dimensões, comparações, interações e hash do PNG.

    Raises:
        AssertionError: Se números, navegação, gráficos ou layout divergirem.
        Error: Se o navegador não conseguir abrir/renderizar os arquivos locais.
    """
    with duckdb.connect(str(RAIZ / "pizza.duckdb"), read_only=True) as con:
        cursor = con.execute("SELECT * FROM marts.kpis")
        kpi = dict(
            zip([c[0] for c in cursor.description], cursor.fetchone(), strict=True)
        )
        snapshot_esperado = {}
        for nome in MARTS:
            cursor = con.execute(f"SELECT * FROM marts.{nome}")
            colunas = [c[0] for c in cursor.description]
            snapshot_esperado[nome] = [
                dict(zip(colunas, linha, strict=True)) for linha in cursor.fetchall()
            ]

    def formato(valor, casas):
        """Formata o resultado do banco independentemente do JavaScript testado."""
        return (
            f"{valor:,.{casas}f}".replace(",", "_").replace(".", ",").replace("_", ".")
        )

    esperados = {
        "receita": formato(kpi["receita"], 2),
        "pedidos": formato(kpi["pedidos"], 0),
        "unidades": formato(kpi["unidades"], 0),
        "ticket": formato(kpi["ticket_medio"], 2),
    }
    erros = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": 1440, "height": 1024}, device_scale_factor=1
        )
        page.on("pageerror", lambda erro: erros.append(str(erro)))
        page.goto((RAIZ / "design/rascunho.html").as_uri(), wait_until="load")
        page.evaluate("document.fonts.ready")
        assert page.locator("#erro").is_hidden(), "Erro de leitura do snapshot"
        snapshot_carregado = page.evaluate("DADOS")

        def canonico(linha):
            """JSON do navegador representa 1.0 como 1, sem alterar seu valor."""
            normalizada = {
                k: int(v) if isinstance(v, float) and v.is_integer() else v
                for k, v in linha.items()
            }
            return json.dumps(normalizada, sort_keys=True, default=str)

        for nome, linhas in snapshot_esperado.items():
            esperadas = sorted(canonico(r) for r in linhas)
            carregadas = sorted(canonico(r) for r in snapshot_carregado[nome])
            assert carregadas == esperadas, f"Snapshot difere do banco: {nome}"
        for id_, esperado in esperados.items():
            assert page.locator(f"#{id_}").inner_text() == esperado, id_
        assert page.locator(".panel .mart-source").count() == 7
        assert page.locator(".answer").count() == 7
        assert page.locator("#mensal circle").count() == 36
        assert page.locator("#horas rect").count() == 19
        assert "116" in page.locator("#sem-hora").inner_text()
        nomes = [r["Name"] for r in snapshot_carregado["concentracao_pizzas"]]
        assert page.locator("#pareto .pareto-label").all_text_contents() == nomes
        assert "São Paulo" in page.locator("#horas svg").get_attribute("aria-label")
        assert "21h" in page.locator("#resposta-horas").inner_text()
        cortes_pareto = page.locator("#pareto .pareto-label").evaluate_all(
            "els => els.filter(el => {const a=el.getBoundingClientRect(); "
            "const b=el.ownerSVGElement.getBoundingClientRect(); "
            "return a.left < b.left-1 || a.right > b.right+1 || "
            "a.bottom > b.bottom+1;}).map(el=>el.textContent)"
        )
        assert not cortes_pareto, f"Nomes do Pareto cortados: {cortes_pareto}"
        page.select_option("#metrica", "pedidos")
        assert "Pedidos" in page.locator("#mensal svg").get_attribute("aria-label")
        assert page.locator("#receita").inner_text() == esperados["receita"]
        page.select_option("#metrica", "receita")
        page.locator('nav a[href="#produtos"]').click()
        assert page.evaluate("location.hash") == "#produtos"
        page.goto((RAIZ / "design/rascunho.html").as_uri(), wait_until="load")
        page.evaluate("document.fonts.ready")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        cortes = page.locator(".value").evaluate_all(
            "els => els.filter(el => el.scrollWidth > el.clientWidth).map(el => el.id)"
        )
        assert not cortes, f"KPIs cortados: {cortes}"
        altura = page.evaluate("document.documentElement.scrollHeight")
        page.screenshot(path=str(RAIZ / "design/rascunho.png"), full_page=True)
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (
            "Transbordamento móvel"
        )
        assert not page.locator(".value").evaluate_all(
            "els => els.filter(el => el.scrollWidth > el.clientWidth).map(el => el.id)"
        ), "KPI cortado no móvel"
        page.screenshot(path=str(RAIZ / "design/rascunho-mobile.png"), full_page=True)
        assert not erros, erros
        browser.close()
    png = RAIZ / "design/rascunho.png"
    relatorio = {
        "capturado_em_utc": datetime.now(UTC).isoformat(),
        "origem": "design/rascunho.html renderizado no Chromium",
        "dimensoes_png": [1440, altura],
        "viewport_desktop": [1440, 1024],
        "viewport_mobile": [390, 844],
        "kpis_conferidos_com_banco": esperados,
        "snapshot_conferido_integralmente": list(MARTS),
        "graficos_com_mart_e_resposta": 7,
        "alternancia_mensal_e_navegacao": "aprovadas",
        "transbordamento_horizontal": False,
        "erros_javascript": erros,
        "png_sha256": hashlib.sha256(png.read_bytes()).hexdigest(),
        "html_sha256": hashlib.sha256(
            (RAIZ / "design/rascunho.html").read_bytes()
        ).hexdigest(),
        "dados_js_sha256": hashlib.sha256(
            (RAIZ / "design/dados.js").read_bytes()
        ).hexdigest(),
    }
    (RAIZ / "design/verificacao.json").write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return relatorio


if __name__ == "__main__":
    print(json.dumps(capturar(), ensure_ascii=False, indent=2))
