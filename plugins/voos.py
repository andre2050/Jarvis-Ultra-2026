"""Plugin: voos — abre o Google Flights com a busca pronta."""
import webbrowser
from urllib.parse import quote_plus

TOOL = {
    "name": "buscar_voos",
    "description": ("Procura passagens aéreas: abre o Google Flights com origem, "
                    "destino e data já preenchidos. Use pra qualquer pedido de voo, "
                    "passagem ou viagem de avião."),
    "parameters": {"type": "object",
                   "properties": {
                       "origem": {"type": "string", "description": "cidade de origem (ex.: São Paulo)"},
                       "destino": {"type": "string", "description": "cidade de destino (ex.: Lisboa)"},
                       "data": {"type": "string",
                                "description": "data ou período (ex.: '12 de outubro', 'dezembro')"},
                   },
                   "required": ["origem", "destino"]},
}


def run(origem: str, destino: str, data: str = "") -> str:
    o = origem.strip()
    d = destino.strip()
    if not o or not d:
        return "preciso de origem e destino, senhor."
    pergunta = f"voos de {o} para {d}"
    if data.strip():
        pergunta += f" em {data.strip()}"
    webbrowser.open(f"https://www.google.com/travel/flights?q={quote_plus(pergunta)}")
    return (f"Google Flights aberto com a busca “{pergunta}”. "
            "Os melhores preços já aparecem na tela, senhor.")
