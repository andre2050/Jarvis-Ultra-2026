"""Cliente Ollama — o cérebro 100% offline do Jarvis Ultra 2026.

Sem internet, sem chave, sem custo. Function calling nativo para
modelos com tools (llama3.1+, qwen2.5, mistral-nemo...).
"""
import json
import os
import shutil
import subprocess
import sys
import time

import requests

TIMEOUT_CHAT = 300  # modelos grandes demoram na primeira resposta


def disponivel(host: str) -> bool:
    try:
        return requests.get(f"{host}/api/tags", timeout=2).status_code == 200
    except Exception:
        return False


def modelos(host: str) -> list:
    try:
        r = requests.get(f"{host}/api/tags", timeout=3)
        return [m.get("name", "") for m in r.json().get("models", [])]
    except Exception:
        return []


def chat(host: str, modelo: str, messages: list, tools: list | None = None) -> dict:
    """Um turno de /api/chat → {"texto": str, "tool_calls": [{name, args}]}"""
    body = {"model": modelo, "messages": list(messages), "stream": False}
    if tools:
        body["tools"] = [{"type": "function", "function": t} for t in tools]
    r = requests.post(f"{host}/api/chat", json=body, timeout=TIMEOUT_CHAT)
    r.raise_for_status()
    msg = r.json().get("message", {}) or {}
    calls = []
    for c in msg.get("tool_calls") or []:
        fn = c.get("function", {}) or {}
        args = fn.get("arguments", {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                args = {}
        if fn.get("name"):
            calls.append({"name": fn["name"], "args": args or {}})
    return {"texto": (msg.get("content") or "").strip(), "tool_calls": calls}


# ---------- servidor: acha, sobe e espera ----------

_CREATE_NO_WINDOW = 0x08000000 if sys.platform.startswith("win") else 0


def _exe_ollama():
    """Acha o binário do Ollama: PATH primeiro, depois caminhos padrão."""
    achado = shutil.which("ollama")
    if achado:
        return achado
    if sys.platform.startswith("win"):
        base = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama")
        for cand in (os.path.join(base, "ollama.exe"), os.path.join(base, "ollama app.exe")):
            if os.path.exists(cand):
                return cand
    else:
        for cand in ("/usr/local/bin/ollama", "/opt/homebrew/bin/ollama",
                     "/Applications/Ollama.app/Contents/Resources/ollama",
                     "/usr/bin/ollama"):
            if os.path.exists(cand):
                return cand
    return None


def instalado() -> bool:
    return _exe_ollama() is not None


def subir_servidor(host: str, esperar_s: int = 20) -> bool:
    """Garante que o servidor Ollama responde. Se não estiver ligado,
    sobe 'ollama serve' em segundo plano e espera. True = conectou."""
    if disponivel(host):
        return True
    exe = _exe_ollama()
    if exe:
        try:
            subprocess.Popen(
                [exe, "serve"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL, creationflags=_CREATE_NO_WINDOW)
        except Exception:
            pass
    prazo = time.time() + esperar_s
    while time.time() < prazo:
        if disponivel(host):
            return True
        time.sleep(0.5)
    return disponivel(host)
