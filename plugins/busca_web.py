"""Plugin: busca na web — DuckDuckGo HTML, sem chave, com extratos."""
import re
import urllib.parse
import urllib.request

TOOL = {
    "name": "buscar_web",
    "description": ("Busca na web (notícias, pesquisa, preço, curiosidades). "
                     "Devolve os 5 melhores resultados com extrato — cite-os na resposta."),
    "parameters": {"type": "object",
                   "properties": {"consulta": {"type": "string",
                                               "description": "o que buscar"}},
                   },
    "required": ["consulta"],
}


def run(consulta: str) -> str:
    try:
        url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(consulta)
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=12) as r:
            html = r.read().decode("utf-8", errors="ignore")
        titulos = re.findall(r'class="result__a"[^>]*>(.*?)</a>', html)[:5]
        extratos = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>|class="result__snippet"[^>]*>(.*?)</td>', html)[:5]
        saida = []
        for i, t in enumerate(titulos):
            limpo = re.sub(r"<[^>]+>", "", t)
            extra = ""
            if i < len(extratos):
                par = extratos[i]
                extra = re.sub(r"<[^>]+>", "", (par[0] or par[1]) if isinstance(par, tuple) else par)[:180]
            saida.append(f"{i + 1}. {limpo}\n   {extra}")
        return "\n".join(saida) if saida else "busca sem resultados — tente outras palavras."
    except Exception as e:
        return f"busca falhou (sem internet?): {str(e)[:90]}"
