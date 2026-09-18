"""Plugin: navegador pro — abrir páginas, clicar em textos e preencher campos (playwright opcional)."""
from pathlib import Path

TOOL = {
    "name": "navegador_pro",
    "description": ("Controla o navegador de verdade: abre um site, clica em um "
                    "texto/botão/link da página, preenche um campo de formulário e "
                    "tira screenshot da página. Requer playwright instalado "
                    "(aviso honesto se faltar)."),
    "parameters": {"type": "object",
                   "properties": {
                       "acao": {"type": "string",
                                "description": "abrir | clicar | preencher | screenshot"},
                       "url": {"type": "string", "description": "endereço do site (acoes: abrir, clicar, preencher)"},
                       "texto": {"type": "string",
                                 "description": "texto do link/botão a clicar, ou texto a digitar (acao=preencher)"},
                       "campo": {"type": "string",
                                 "description": "nome/placeholder do campo a preencher (acao=preencher)"}},
                   },
    "required": ["acao"],
}

_PAGE = None  # aba viva entre chamadas


def _pagina():
    global _PAGE
    if _PAGE is not None:
        return _PAGE
    from playwright.sync_api import sync_playwright
    contexto = sync_playwright().start()
    navegador = contexto.chromium.launch(headless=False)
    _PAGE = navegador.new_page()
    return _PAGE


def run(acao: str, url: str = "", texto: str = "", campo: str = "") -> str:
    a = (acao or "").strip().lower()
    try:
        pagina = _pagina()
    except Exception:
        return ("playwright não está instalado, senhor. Instale com:\n"
                "pip install playwright && playwright install chromium")
    try:
        if a == "abrir":
            if not url.strip():
                return "qual site, senhor?"
            pagina.goto(url.strip(), timeout=30000)
            return f"aberto: {pagina.title()} ({url.strip()})"
        if a == "clicar":
            if url.strip():
                pagina.goto(url.strip(), timeout=30000)
            if not texto.strip():
                return "clicar em quê? Me diga o texto do link/botão."
            pagina.get_by_text(texto.strip(), exact=False).first.click(timeout=15000)
            return f"cliquei em “{texto.strip()}” — página: {pagina.title()}"
        if a == "preencher":
            if url.strip():
                pagina.goto(url.strip(), timeout=30000)
            alvo = campo.strip() or texto.strip()
            if not alvo or not texto.strip():
                return "me diga o campo e o texto, senhor."
            pagina.get_by_placeholder(alvo).first.fill(texto.strip(), timeout=15000)
            return f"preenchido “{alvo}” com: {texto.strip()[:60]}"
        if a == "screenshot":
            arq = Path.home() / ".jarvis_ultra" / "pagina.png"
            arq.parent.mkdir(parents=True, exist_ok=True)
            pagina.screenshot(path=str(arq))
            return f"screenshot da página salvo em {arq}"
        return "ações: abrir, clicar, preencher, screenshot"
    except Exception as e:
        return f"não deu pra {a} no navegador: {e}"
