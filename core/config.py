"""Configurações persistidas — ~/.jarvis_ultra_2026/config.json"""
import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".jarvis_ultra_2026"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS = {
    "usuario": "André",
    "nome_assistente": "Jarvis",
    "cerebro": "ollama",              # 100% offline desde o nascimento
    "ollama_host": "http://localhost:11434",
    "ollama_model": "llama3.2",
    "voz_ativa": True,
    "voz_velocidade": 0.85,           # mordomo: mais lento
    "voz_volume": 1.0,
    "voz_id": "",                     # "" = automática
    "cor": "#00e5c7",                 # HUD recolorível por hex (tematização ao vivo)
}


def load() -> dict:
    cfg = dict(DEFAULTS)
    try:
        if CONFIG_FILE.exists():
            cfg.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
    except Exception:
        pass
    return cfg


def save(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
