"""Plugin: hardware — telemetria de CPU, RAM e temperatura com alertas."""
import platform

try:
    import psutil
    TEM_PSUTIL = True
except ImportError:
    psutil = None
    TEM_PSUTIL = False

TOOL = {
    "name": "hardware",
    "description": ("Monitoramento do hardware: CPU, RAM e temperatura em tempo real. "
                     "Use quando perguntarem o status da máquina ou se algo estiver lento."),
    "parameters": {"type": "object", "properties": {}},
}


def run() -> str:
    if not TEM_PSUTIL:
        return ("telemetria completa pede psutil — rode: pip install psutil. "
                f"Parcial: {platform.system()} {platform.release()}, "
                f"{platform.processor() or 'CPU não identificada'}.")
    cpu = psutil.cpu_percent(interval=0.6)
    ram = psutil.virtual_memory()
    disco = psutil.disk_usage("/")
    linhas = [f"CPU em {cpu:.0f}%",
              f"RAM {ram.used / 1e9:.1f} de {ram.total / 1e9:.1f} GB ({ram.percent:.0f}%)",
              f"disco {disco.percent:.0f}% cheio"]
    alertas = []
    if cpu > 85:
        alertas.append("CPU crítica — algo pesado rodando")
    if ram.percent > 90:
        alertas.append("RAM quase no limite")
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            nome, val = list(temps.items())[0][0], list(temps.items())[0][1][0]
            linhas.insert(0, f"{nome} {val.current:.0f}°C")
            if val.current > 80:
                alertas.append("temperatura alta")
    except (AttributeError, Exception):
        pass
    status = ". ".join(linhas) + "."
    if alertas:
        status += " ALERTA: " + "; ".join(alertas) + "."
    return status
