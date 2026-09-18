"""Plugin: controlar o PC — digitar, clicar, atalhos, rolar e capturas (pyautogui opcional)."""

TOOL = {
    "name": "controlar_pc",
    "description": ("Controla o computador direto: digitar texto, clicar, atalhos de "
                    "teclado, apertar tecla, rolar a tela e tirar screenshot. "
                    "Requer pyautogui instalado (aviso honesto se faltar)."),
    "parameters": {"type": "object",
                   "properties": {
                       "acao": {"type": "string",
                                "description": "digitar | clicar | atalho | tecla | rolar | screenshot"},
                       "texto": {"type": "string", "description": "texto a digitar (acao=digitar)"},
                       "x": {"type": "integer", "description": "posição horizontal do clique"},
                       "y": {"type": "integer", "description": "posição vertical do clique"},
                       "teclas": {"type": "string",
                                  "description": "teclas do atalho separadas por + (ex.: ctrl+shift+esc)"},
                       "tecla": {"type": "string",
                                 "description": "tecla a apertar (ex.: enter, win, esc, tab)"},
                       "direcao": {"type": "string",
                                   "description": "cima ou baixo (acao=rolar)"}},
                   },
    "required": ["acao"],
}


def _pyautogui():
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05
    return pyautogui


def run(acao: str, texto: str = "", x: int = -1, y: int = -1,
        teclas: str = "", tecla: str = "", direcao: str = "baixo") -> str:
    a = (acao or "").strip().lower()
    try:
        ag = _pyautogui()
    except Exception:
        return ("pyautogui não está instalado, senhor. "
                "Instale com: pip install pyautogui")
    try:
        if a == "digitar":
            if not texto:
                return "nada pra digitar — me passe o texto."
            ag.typewrite(texto, interval=0.04)
            return f"digitado: {texto[:60]}"
        if a == "clicar":
            if x >= 0 and y >= 0:
                ag.click(x, y)
                return f"clique em ({x}, {y})"
            ag.click()
            return "clique na posição atual do mouse"
        if a == "atalho":
            if not teclas:
                return "quais teclas, senhor? (ex.: ctrl+shift+esc)"
            ag.hotkey(*[t.strip().lower() for t in teclas.split("+")])
            return f"atalho executado: {teclas}"
        if a == "tecla":
            if not tecla:
                return "qual tecla, senhor? (ex.: enter, esc, win)"
            ag.press(tecla.strip().lower())
            return f"tecla apertada: {tecla}"
        if a == "rolar":
            qtd = -600 if direcao.strip().lower() == "baixo" else 600
            ag.scroll(qtd)
            return f"rolado pra {direcao}"
        if a == "screenshot":
            arq = ag.screenshot()
            destino = f"jarvis_screenshot_{__import__('time').strftime('%H%M%S')}.png"
            arq.save(destino)
            return f"screenshot salvo como {destino} na pasta do app"
        return "ações: digitar, clicar, atalho, tecla, rolar, screenshot"
    except Exception as e:
        return f"não deu pra {a}: {e}"
