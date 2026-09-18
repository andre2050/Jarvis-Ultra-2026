"""Visemas — dublagem real, boca sem idioma.

A articulação vem da REDUÇÃO UNICODE do texto: todo caractere é
reduzido (NFD, sem acentos, transliterado quando cirílico/grego) e
mapeado pra uma forma de boca. Um único conjunto de regras serve
latino, cirílico e grego — alfabetos que ocultam a pronúncia
recorrem a eles sem problema.

Formas de boca (visemas): fechamentos (MM), aberturas (AA) e
arredondamentos (OH/UH) — não um medidor de volume.
"""
import unicodedata

# ---------- transliteração mínima (cirílico + grego → latino) ----------

_TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "i", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sh",
    "ы": "i", "э": "e", "ю": "iu", "я": "ia",
    "α": "a", "β": "v", "γ": "g", "δ": "d", "ε": "e", "ζ": "z", "η": "i",
    "θ": "th", "ι": "i", "κ": "k", "λ": "l", "μ": "m", "ν": "n", "ξ": "ks",
    "ο": "o", "π": "p", "ρ": "r", "σ": "s", "ς": "s", "τ": "t", "υ": "u",
    "φ": "f", "χ": "kh", "ψ": "ps", "ω": "o",
}


def reduzir(texto: str) -> str:
    """Reduz qualquer alfabeto suportado a uma sequência base latinizada."""
    t = unicodedata.normalize("NFD", texto.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return "".join(_TRANSLIT.get(c, c) for c in t)


# ---------- mapa fonético → visema ----------
# MM fechado · AA aberto · EH meio-aberto · IH largo raso · OH arredondado
# UH arredondado fechado · FF labiodental · SS fresta

_VOGAIS = {"a": "AA", "e": "EH", "i": "IH", "o": "OH", "u": "UH", "y": "IH", "w": "UH"}
_BILABIAIS = {"m": "MM", "b": "MM", "p": "MM"}
_LABIODENTAIS = {"f": "FF", "v": "FF"}
_FRESTA = {"s", "z", "c", "x", "j", "t", "d", "k", "g", "r", "l", "n", "h", "q"}


def _visema(c: str) -> str:
    if c in _VOGAIS:
        return _VOGAIS[c]
    if c in _BILABIAIS:
        return "MM"
    if c in _LABIODENTAIS:
        return "FF"
    if c in _FRESTA:
        return "SS"
    return ""


def frase_para_visemas(texto: str, velocidade: float = 0.85) -> list:
    """Transforma uma frase numa agenda de formas de boca.

    Devolve [(visema, duracao_s), ...] pronta pro avatar consumir em
    tempo real — ~50 formas por segundo na interpolação do desenho.
    Pausas naturais em vírgulas e pontos.
    """
    base = 0.062 / max(0.5, velocidade)     # duração base por fonema
    agenda, buf, dur = [], "", 0.0
    for ch in reduzir(texto):
        if ch in " ,;":
            if buf:
                agenda.append((buf, dur))
                buf, dur = "", 0.0
            agenda.append(("MM", base * 1.6))
        elif ch in ".!?…:":
            if buf:
                agenda.append((buf, dur))
                buf, dur = "", 0.0
            agenda.append(("MM", base * 4.0))
        else:
            v = _visema(ch)
            if not v:
                continue
            if v == buf:
                dur += base * 0.6           # mesma forma: soma suave
            else:
                if buf:
                    agenda.append((buf, dur))
                buf, dur = v, base
    if buf:
        agenda.append((buf, dur))
    if not agenda:
        agenda = [("MM", 0.2)]
    return agenda


def duracao_estimada(texto: str, velocidade: float = 0.85) -> float:
    """Segundos que a agenda completa deve durar — sincronia com a voz."""
    return sum(d for _, d in frase_para_visemas(texto, velocidade))
