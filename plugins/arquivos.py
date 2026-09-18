"""Plugin: processador de arquivos — leia, resuma e responda sobre arquivos locais."""
from pathlib import Path

TOOL = {
    "name": "arquivos",
    "description": ("Lê um arquivo local de texto (.txt, .md, .py, .json, .csv, .log) "
                     "e devolve o conteúdo/trecho pra eu analisar, resumir ou responder "
                     "perguntas sobre ele. Aceita procurar uma palavra dentro do arquivo."),
    "parameters": {"type": "object",
                   "properties": {
                       "caminho": {"type": "string", "description": "caminho do arquivo"},
                       "procurar": {"type": "string",
                                    "description": "palavra a procurar (opcional)"}},
                   },
    "required": ["caminho"],
}

_EXT_OK = {".txt", ".md", ".py", ".json", ".csv", ".log", ".xml", ".html", ".css", ".js", ".ini", ".cfg"}


def run(caminho: str, procurar: str = "") -> str:
    p = Path(caminho.strip().strip('"'))
    if not p.exists():
        # tolerância: procura na pasta pessoal
        cand = list(Path.home().glob("**/" + p.name))[:1]
        if cand:
            p = cand[0]
        else:
            return f"arquivo não encontrado: {caminho}"
    if p.suffix.lower() not in _EXT_OK:
        return f"formato {p.suffix} não suportado — só arquivos de texto."
    try:
        texto = p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"não consegui abrir: {str(e)[:90]}"
    linhas = texto.count("\n") + 1
    palavras = len(texto.split())
    if procurar:
        achados = [ln.strip()[:160] for ln in texto.split("\n")
                   if procurar.lower() in ln.lower()][:12]
        if not achados:
            return f"{p.name}: {linhas} linhas, {palavras} palavras — '{procurar}' não aparece."
        return f"{p.name}: '{procurar}' em {len(achados)} linha(s):\n" + "\n".join(achados)
    trecho = texto[:2200]
    return (f"{p.name} — {linhas} linhas, {palavras} palavras.\n"
            f"INÍCIO DO ARQUIVO:\n{trecho}")
