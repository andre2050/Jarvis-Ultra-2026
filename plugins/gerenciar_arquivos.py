"""Plugin: gerenciar arquivos e pastas — listar, criar, mover, copiar, apagar, procurar."""
import shutil as _shutil
from pathlib import Path

TOOL = {
    "name": "gerenciar_arquivos",
    "description": ("Gerencia arquivos e pastas do computador: listar pasta, criar "
                    "pasta/arquivo, escrever em arquivo, ler arquivo, mover, copiar, "
                    "renomear, apagar (manda pra lixeira quando dá) e procurar por nome."),
    "parameters": {"type": "object",
                   "properties": {
                       "acao": {"type": "string",
                                "description": "listar | criar | escrever | ler | mover | copiar | renomear | apagar | procurar"},
                       "caminho": {"type": "string", "description": "caminho do arquivo ou pasta"},
                       "destino": {"type": "string", "description": "destino (mover/copiar/renomear)"},
                       "conteudo": {"type": "string", "description": "texto a escrever (acao=escrever)"}},
                   },
    "required": ["acao", "caminho"],
}


def _p(caminho: str) -> Path:
    p = Path(caminho.strip().strip('"'))
    if not p.is_absolute():
        p = Path.home() / p
    return p


def _lixeira(p: Path) -> str:
    try:
        from send2trash import send2trash
        send2trash(str(p))
        return "apagado (na lixeira, recuperável)"
    except Exception:
        if p.is_dir():
            _shutil.rmtree(p)
        else:
            p.unlink()
        return "apagado (definitivo)"


def run(acao: str, caminho: str, destino: str = "", conteudo: str = "") -> str:
    a = (acao or "").strip().lower()
    p = _p(caminho)
    try:
        if a == "listar":
            if not p.is_dir():
                return f"'{caminho}' não é uma pasta"
            itens = sorted(p.iterdir(), key=lambda i: i.name.lower())
            linhas = [f"{'[pasta] ' if i.is_dir() else ''}{i.name}" for i in itens[:60]]
            total = len(itens)
            return (f"{total} itens em {p}:\n" + "\n".join(linhas)
                    + (f"\n(…e mais {total - 60})" if total > 60 else ""))
        if a == "criar":
            if "." in p.name:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.touch()
                return f"arquivo criado: {p}"
            p.mkdir(parents=True, exist_ok=True)
            return f"pasta criada: {p}"
        if a == "escrever":
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "a", encoding="utf-8") as f:
                f.write(conteudo + "\n")
            return f"escrito em {p}"
        if a == "ler":
            texto = p.read_text(encoding="utf-8", errors="replace")
            return f"{p}:\n{texto[:3000]}" + ("…" if len(texto) > 3000 else "")
        if a == "mover":
            d = _p(destino)
            _shutil.move(str(p), str(d))
            return f"movido: {p.name} → {d}"
        if a == "copiar":
            d = _p(destino)
            if p.is_dir():
                _shutil.copytree(str(p), str(d))
            else:
                _shutil.copy2(str(p), str(d))
            return f"copiado: {p.name} → {d}"
        if a == "renomear":
            novo = p.with_name(destino.strip())
            p.rename(novo)
            return f"renomeado: {p.name} → {novo.name}"
        if a == "apagar":
            if not p.exists():
                return f"'{caminho}' não existe"
            return _lixeira(p) + f": {p}"
        if a == "procurar":
            if not p.is_dir():
                return f"'{caminho}' não é uma pasta"
            achados = [str(i) for i in p.rglob(destino.strip())][:30]
            return (f"{len(achados)} resultado(s):\n" + "\n".join(achados)
                    if achados else f"nada com “{destino}” dentro de {p}")
        return (f"ação “{acao}” desconhecida. Use: listar, criar, escrever, ler, "
                "mover, copiar, renomear, apagar ou procurar.")
    except FileNotFoundError:
        return f"caminho não encontrado: {caminho}"
    except Exception as e:
        return f"não deu pra {a} “{caminho}”: {e}"
