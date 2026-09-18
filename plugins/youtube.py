"""Plugin: YouTube — tocar, pesquisar e abrir em alta, direto no navegador."""
import webbrowser
from urllib.parse import quote_plus

TOOL = {
    "name": "youtube",
    "description": ("Abre o YouTube: toca/pesquisa um vídeo ou artista, ou mostra os "
                    "em alta. Use pra qualquer pedido de música ou vídeo do YouTube."),
    "parameters": {"type": "object",
                   "properties": {
                       "pedido": {"type": "string",
                                  "description": "o que tocar ou pesquisar (ex.: 'Iron Man soundtrack')"},
                       "acao": {"type": "string",
                                "description": "tocar (padrão), pesquisar ou em_alta"}},
                   },
}


def run(pedido: str = "", acao: str = "tocar") -> str:
    a = (acao or "tocar").strip().lower()
    if a in ("alta", "trending", "em alta", "em_alta"):
        webbrowser.open("https://www.youtube.com/feed/trending")
        return "YouTube em alta aberto, senhor."
    termo = pedido.strip()
    if not termo:
        webbrowser.open("https://www.youtube.com")
        return "YouTube aberto, senhor."
    if a == "pesquisar":
        webbrowser.open(f"https://www.youtube.com/results?search_query={quote_plus(termo)}")
        return f"pesquisa aberta no YouTube: {termo}"
    webbrowser.open(f"https://www.youtube.com/results?search_query={quote_plus(termo)}")
    return (f"YouTube aberto com “{termo}” — o primeiro resultado já é o play, senhor.")
