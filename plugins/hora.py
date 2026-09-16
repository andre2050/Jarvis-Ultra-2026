"""Plugin: hora e data — briefing de tempo."""
from datetime import datetime

TOOL = {
    "name": "hora_agora",
    "description": "Retorna data, hora e dia da semana atuais do computador.",
    "parameters": {"type": "object", "properties": {}},
}

def run() -> str:
    agora = datetime.now()
    dias = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
    return f"{dias[agora.weekday()]}, {agora.strftime('%d/%m/%Y %H:%M')}"
