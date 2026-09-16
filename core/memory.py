"""Memória persistente — ilimitada, nada esquecido em silêncio.

Tudo fica em ~/.jarvis_ultra_2026/memoria.json; o prompt exibe o resumo,
o resto é buscado sob demanda (busca local por palavra-chave).
"""
import json
from datetime import datetime

from core.config import CONFIG_DIR

ARQUIVO = CONFIG_DIR / "memoria.json"


def _ler() -> list:
    try:
        return json.loads(ARQUIVO.read_text(encoding="utf-8"))
    except Exception:
        return []


def _gravar(itens: list) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    ARQUIVO.write_text(json.dumps(itens, indent=1, ensure_ascii=False), encoding="utf-8")


def salvar(texto: str) -> str:
    itens = _ler()
    itens.append({"texto": texto.strip(), "quando": datetime.now().strftime("%Y-%m-%d %H:%M")})
    _gravar(itens)
    return "memorizado."


def todos() -> list:
    return _ler()


def buscar(termo: str) -> list:
    t = termo.strip().lower()
    return [i for i in _ler() if t in i["texto"].lower() or t in i["quando"].lower()]


def apagar(indice: int) -> str:
    itens = _ler()
    if 0 <= indice < len(itens):
        removido = itens.pop(indice)
        _gravar(itens)
        return f"apagado: {removido['texto'][:60]}"
    return "índice inválido."


def apagar_tudo() -> str:
    _gravar([])
    return "memória zerada."
