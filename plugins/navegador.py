"""Plugin: controle de navegador — abre sites e buscas."""
import webbrowser

TOOL = {
    "name": "abrir_navegador",
    "description": ("Abre uma URL no navegador padrão. Se o valor não parecer um site, "
                    "abre uma busca do DuckDuckGo com o termo."),
    "parameters": {
        "type": "object",
        "properties": {
            "alvo": {"type": "string", "description": "URL (ex: github.com) ou termo de busca"}
        },
        "required": ["alvo"],
    },
}

def run(alvo: str) -> str:
    alvo = (alvo or "").strip()
    if not alvo:
        return "nada para abrir"
    if " " in alvo or "." not in alvo:
        webbrowser.open(f"https://duckduckgo.com/?q={alvo.replace(' ', '+')}")
        return f"busca aberta: {alvo}"
    if not alvo.startswith("http"):
        alvo = "https://" + alvo
    webbrowser.open(alvo)
    return f"aberto: {alvo}"
