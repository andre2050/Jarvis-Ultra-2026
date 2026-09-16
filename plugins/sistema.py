"""Plugin: telemetria de hardware — CPU, RAM e bateria."""
import psutil

TOOL = {
    "name": "telemetria",
    "description": ("Lê CPU, memória RAM e bateria do computador em tempo real. "
                    "Use para status do sistema e alertas de hardware."),
    "parameters": {"type": "object", "properties": {}},
}

def run() -> str:
    cpu = psutil.cpu_percent(interval=0.4)
    ram = psutil.virtual_memory()
    txt = f"CPU {cpu:.0f}% · RAM {ram.percent:.0f}% de {ram.total // (1 << 30)} GB"
    bateria = psutil.sensors_battery()
    if bateria:
        txt += f" · bateria {bateria.percent:.0f}%" + ("" if bateria.powered else " (descarregando)")
    return txt
