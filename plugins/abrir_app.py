"""Plugin: abrir aplicativos — lê o pedido e abre o programa (Windows, Mac, Linux)."""
import os
import platform
import shutil
import subprocess
import time

TOOL = {
    "name": "abrir_app",
    "description": ("Abre qualquer aplicativo instalado no computador. Use quando o "
                    "usuário pedir pra abrir, lançar ou iniciar um programa "
                    "(ex.: 'abre o Chrome', 'abre o bloco de notas')."),
    "parameters": {"type": "object",
                   "properties": {
                       "nome": {"type": "string",
                                "description": "nome do app (ex.: chrome, vscode, whatsapp)"}},
                   },
    "required": ["nome"],
}

_SISTEMA = platform.system()

_ALIASES = {
    "chrome":             {"Windows": "chrome",                "Darwin": "Google Chrome",      "Linux": "google-chrome"},
    "google chrome":      {"Windows": "chrome",                "Darwin": "Google Chrome",      "Linux": "google-chrome"},
    "firefox":            {"Windows": "firefox",               "Darwin": "Firefox",           "Linux": "firefox"},
    "edge":               {"Windows": "msedge",                 "Darwin": "Microsoft Edge",     "Linux": "microsoft-edge"},
    "navegador":          {"Windows": "chrome",                "Darwin": "Safari",             "Linux": "firefox"},
    "whatsapp":          {"Windows": "WhatsApp",              "Darwin": "WhatsApp",           "Linux": "whatsapp"},
    "telegram":          {"Windows": "Telegram",              "Darwin": "Telegram",           "Linux": "telegram"},
    "discord":           {"Windows": "Discord",                "Darwin": "Discord",            "Linux": "discord"},
    "spotify":           {"Windows": "Spotify",                "Darwin": "Spotify",            "Linux": "spotify"},
    "youtube":           {"Windows": "https://youtube.com",    "Darwin": "https://youtube.com","Linux": "https://youtube.com"},
    "netflix":           {"Windows": "Netflix",                "Darwin": "Netflix",           "Linux": "firefox"},
    "vscode":            {"Windows": "code",                   "Darwin": "Visual Studio Code", "Linux": "code"},
    "visual studio code": {"Windows": "code",                  "Darwin": "Visual Studio Code", "Linux": "code"},
    "terminal":          {"Windows": "wt",                    "Darwin": "Terminal",           "Linux": "x-terminal-emulator"},
    "cmd":               {"Windows": "cmd.exe",                "Darwin": "Terminal",           "Linux": "bash"},
    "powershell":        {"Windows": "powershell.exe",         "Darwin": "Terminal",           "Linux": "bash"},
    "bloco de notas":    {"Windows": "notepad.exe",            "Darwin": "TextEdit",           "Linux": "gedit"},
    "notepad":           {"Windows": "notepad.exe",            "Darwin": "TextEdit",           "Linux": "gedit"},
    "calculadora":       {"Windows": "calc.exe",               "Darwin": "Calculator",         "Linux": "gnome-calculator"},
    "explorador":        {"Windows": "explorer.exe",           "Darwin": "Finder",             "Linux": "nautilus"},
    "explorador de arquivos": {"Windows": "explorer.exe",     "Darwin": "Finder",             "Linux": "nautilus"},
    "paint":             {"Windows": "mspaint.exe",            "Darwin": "Preview",            "Linux": "gimp"},
    "word":              {"Windows": "winword",                "Darwin": "Microsoft Word",     "Linux": "libreoffice"},
    "excel":             {"Windows": "excel",                  "Darwin": "Microsoft Excel",   "Linux": "libreoffice"},
    "powerpoint":        {"Windows": "powerpnt",                "Darwin": "Microsoft PowerPoint", "Linux": "libreoffice"},
    "steam":             {"Windows": "steam",                 "Darwin": "Steam",              "Linux": "steam"},
    "figma":             {"Windows": "Figma",                  "Darwin": "Figma",              "Linux": "figma"},
    "configurações":     {"Windows": "ms-settings:",           "Darwin": "System Preferences", "Linux": "gnome-control-center"},
}


def _resolve(pedido: str) -> str:
    chave = pedido.lower().strip()
    if chave in _ALIASES:
        return _ALIASES[chave].get(_SISTEMA, pedido)
    for apelido, mapa in _ALIASES.items():
        if apelido in chave or chave in apelido:
            return mapa.get(_SISTEMA, pedido)
    return pedido


def _windows(nome: str) -> bool:
    if nome.startswith("http"):
        os.startfile(nome)
        return True
    if shutil.which(nome) or shutil.which(nome.split(".")[0]):
        subprocess.Popen(nome, shell=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    if ":" in nome:  # ex.: ms-settings:
        os.startfile(nome)
        return True
    try:  # última tentativa: menu Iniciar via teclado
        import pyautogui
        pyautogui.press("win")
        time.sleep(0.7)
        pyautogui.write(nome, interval=0.05)
        time.sleep(0.9)
        pyautogui.press("enter")
        time.sleep(2.0)
        return True
    except Exception:
        return False


def _mac(nome: str) -> bool:
    r = subprocess.run(["open", "-a", nome], capture_output=True, timeout=8)
    if r.returncode == 0:
        return True
    binario = shutil.which(nome.lower())
    if binario:
        subprocess.Popen([binario], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    return False


def _linux(nome: str) -> bool:
    binario = shutil.which(nome) or shutil.which(nome.lower())
    if binario:
        subprocess.Popen([binario], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    return False


def run(nome: str) -> str:
    alvo = _resolve(nome)
    if _SISTEMA == "Windows":
        ok = _windows(alvo)
    elif _SISTEMA == "Darwin":
        ok = _mac(alvo)
    else:
        ok = _linux(alvo)
    if ok:
        return f"aberto: {nome}"
    return (f"não consegui abrir '{nome}', senhor. Confira o nome do programa, "
            "ou instale-o primeiro.")
