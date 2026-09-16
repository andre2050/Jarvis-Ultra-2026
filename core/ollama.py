"""Cliente Ollama — o cérebro 100% offline do Jarvis Ultra 2026.

Sem internet, sem chave, sem custo. Function calling nativo para
modelos com tools (llama3.1+, qwen2.5, mistral-nemo...).
"""
import json

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
