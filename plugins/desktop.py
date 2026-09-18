"""Plugin: área de trabalho — trocar papel de parede, listar e ver estatísticas."""
import ctypes
import platform
import subprocess
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

TOOL = {
    "name": "desktop",
    "description": ("Cuida da área de trabalho: trocar o papel de parede (caminho "
                    "local ou URL), listar o que tem na área e contar arquivos/pastas."),
    "parameters": {"type": "object",
                   "properties": {
                       "acao": {"type": "string",
                                "description": "papel_parede | listar | info"},
                       "caminho": {"type": "string",
                                   "description": "caminho da imagem ou URL (acao=papel_parede)"}},
                   },
    "required": ["acao"],
}

_WINDOWS = platform.system() == "Windows"
_DESKTOP = None
for _cand in ["Desktop", "OneDrive/Desktop", "OneDrive/Área de Trabalho", "Área de Trabalho"]:
    if (Path.home() / _cand).exists():
        _DESKTOP = Path.home() / _cand
        break


def _wallpaper_windows(imagem: Path) -> str:
    ctypes.windll.user32.SystemParametersInfoW(20, 0, str(imagem), 3)
    return f"papel de parede trocado: {imagem.name}"


def _wallpaper_mac(imagem: Path) -> str:
    script = (f'tell application "System Events" to tell every desktop to '
              f'set picture to POSIX file "{imagem}"')
    subprocess.run(["osascript", "-e", script], capture_output=True)
    return f"papel de parede trocado: {imagem.name}"


def _wallpaper_linux(imagem: Path) -> str:
    subprocess.run(["gsettings", "set", "org.gnome.desktop.background",
                   "picture-uri", f"file://{imagem}"], capture_output=True)
    return f"papel de parede trocado: {imagem.name}"


def run(acao: str, caminho: str = "") -> str:
    a = (acao or "").strip().lower()
    if a == "listar" or a == "info":
        if _DESKTOP is None:
            return "não achei sua área de trabalho"
        itens = sorted(_DESKTOP.iterdir(), key=lambda i: i.name.lower())
        pastas = [i for i in itens if i.is_dir()]
        arquivos = [i for i in itens if not i.is_dir()]
        if a == "info":
            return (f"área de trabalho: {len(pastas)} pastas e {len(arquivos)} arquivos")
        linhas = [f"{'[pasta] ' if i.is_dir() else ''}{i.name}" for i in itens[:60]]
        return f"{len(itens)} itens:\n" + "\n".join(linhas)
    if a == "papel_parede":
        if not caminho.strip():
            return "me passe o caminho da imagem ou a URL, senhor."
        origem = caminho.strip().strip('"')
        try:
            if origem.startswith("http"):
                ext = Path(urlparse(origem).path).suffix or ".jpg"
                img = Path.home() / ".jarvis_ultra" / f"wallpaper{ext}"
                img.parent.mkdir(parents=True, exist_ok=True)
                with urllib.request.urlopen(origem, timeout=20) as r, open(img, "wb") as f:
                    f.write(r.read())
            else:
                img = Path(origem)
                if not img.is_absolute():
                    img = Path.home() / img
            if not img.exists():
                return f"imagem não encontrada: {origem}"
            if _WINDOWS:
                return _wallpaper_windows(img)
            if platform.system() == "Darwin":
                return _wallpaper_mac(img)
            return _wallpaper_linux(img)
        except Exception as e:
            return f"não deu pra trocar o papel de parede: {e}"
    return "ações: papel_parede, listar, info"
