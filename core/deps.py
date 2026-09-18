"""Degraus de instalação — a voz fica pronta sem manual.

Na primeira execução, se as libs de microfone/escuta não existirem,
o app instala sozinho via pip e relança. Nada de 'pip install' na mão.
"""
import importlib.util
import subprocess
import sys

# (pacote pip, nome p/ importar) — só o trio essencial da voz
ESSENCIAIS = [
    ("sounddevice", "sounddevice"),
    ("vosk", "vosk"),
    ("keyboard", "keyboard"),
]


def instalado(nome_import: str) -> bool:
    """Confere sem importar (importar sounddevice sem áudio lança erro)."""
    try:
        return importlib.util.find_spec(nome_import) is not None
    except Exception:
        return False


def faltando() -> list:
    return [(pip, imp) for pip, imp in ESSENCIAIS if not instalado(imp)]


def instalar(pacotes: list, ao_log=None) -> bool:
    """Instala via pip no mesmo interpretador. True se o pip rodou limpo."""
    if not pacotes:
        return True
    if ao_log:
        ao_log(f"instalando {', '.join(pacotes)}… (uma vez só, ~45 MB)")
    try:
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        r = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "--quiet", *pacotes],
            timeout=900, creationflags=flags, check=False)
        ok = r.returncode == 0
        if ao_log:
            ao_log("voz instalada ✓ — reiniciando…" if ok
                   else "não consegui instalar — seguindo sem escuta")
        return ok
    except Exception as e:
        if ao_log:
            ao_log(f"erro ao instalar: {str(e)[:80]}")
        return False
