"""Plugin: memória persistente — salvar, buscar, apagar."""
from core import memory

TOOL = {
    "name": "memoria",
    "description": ("Gerencia a memória de longo prazo do usuário. Ações: 'salvar' (grava um "
                    "fato/preferência), 'buscar' (recupera por termo), 'listar' (tudo), "
                    "'apagar' (índice) e 'zerar' (apaga tudo)."),
    "parameters": {
        "type": "object",
        "properties": {
            "acao": {"type": "string", "enum": ["salvar", "buscar", "listar", "apagar", "zerar"]},
            "conteudo": {"type": "string", "description": "texto pra salvar ou termo pra buscar"},
            "indice": {"type": "integer", "description": "índice para apagar"},
        },
        "required": ["acao"],
    },
}

def run(acao: str, conteudo: str = "", indice: int = -1) -> str:
    if acao == "salvar":
        return memory.salvar(conteudo) if conteudo else "nada para salvar"
    if acao == "buscar":
        achados = memory.buscar(conteudo)
        return " | ".join(f"[{i}] {m['texto']}" for i, m in enumerate(achados)) or "nada encontrado"
    if acao == "listar":
        return " | ".join(f"[{i}] {m['texto']}" for i, m in enumerate(memory.todos())) or "memória vazia"
    if acao == "apagar":
        return memory.apagar(indice)
    if acao == "zerar":
        return memory.apagar_tudo()
    return "ação inválida"
