"""Plugin: lembretes — agenda um aviso que aparece na tela na hora certa (Windows)."""
import platform
import subprocess
from datetime import datetime, timedelta
from pathlib import Path


TOOL = {
    "name": "criar_lembrete",
    "description": ("Cria um lembrete que aparece na tela do computador na hora marcada. "
                    "Recebe o momento (aceita 'HH:MM', 'HH:MM de dd/mm', 'dd/mm/aaaa HH:MM' "
                    "ou 'em N minutos') e a mensagem."),
    "parameters": {"type": "object",
                   "properties": {
                       "quando": {"type": "string",
                                  "description": "momento do lembrete (ex.: '14:30', 'em 20 minutos', '09/10/2026 08:00')"},
                       "mensagem": {"type": "string",
                                   "description": "texto do lembrete (ex.: 'reunião com o banco')"}},
                   },
    "required": ["quando", "mensagem"],
}

_WINDOWS = platform.system() == "Windows"
_PASTA = Path.home() / ".jarvis_ultra" / "lembretes"


def _interpretar_quando(quando: str):
    q = quando.lower().strip()
    agora = datetime.now()
    try:
        if "minuto" in q:
            n = int("".join(c for c in q if c.isdigit()) or "10")
            return agora + timedelta(minutes=n)
        if "hora" in q and "em" in q:
            n = int("".join(c for c in q.split("em")[1] if c.isdigit()) or "1")
            return agora + timedelta(hours=n)
        fmts = ["%d/%m/%Y %H:%M", "%d/%m/%Y %H", "%d/%m %H:%M", "%d/%m %H", "%H:%M"]
        for fmt in fmts:
            try:
                dt = datetime.strptime(q, fmt)
                if fmt == "%H:%M":  # só hora: hoje (ou amanhã se já passou)
                    dt = dt.combine(agora.date(), dt.time())
                    if dt <= agora:
                        dt += timedelta(days=1)
                elif "%Y" not in fmt:  # sem ano: usa o ano atual
                    dt = dt.replace(year=agora.year)
                return dt
            except ValueError:
                continue
    except Exception:
        pass
    return None


def _agendar_windows(dt: datetime, mensagem: str) -> str:
    _PASTA.mkdir(parents=True, exist_ok=True)
    nome = f"lembrete_{dt.strftime('%Y%m%d_%H%M')}"
    vbs = _PASTA / f"{nome}.vbs"
    vbs.write_text(
        'msg = "' + mensagem.replace('"', "'").strip() + '"\n'
        'Set sh = CreateObject("WScript.Shell")\n'
        'res = sh.Popup("J.A.R.V.I.S: " & msg & vbCrLf & vbCrLf &'
        ' "(' + dt.strftime("%d/%m/%Y %H:%M") + ')", 60, "Lembrete", 64)\n'
        'If res = -1 Then sh.LogEvent 4, "Lembrete exibido: " & msg\n',
        encoding="utf-8")
    r = subprocess.run(
        ["schtasks", "/Create", "/F", "/SC", "ONCE",
         "/TN", nome, "/TR", f'wscript.exe //B "{vbs}"',
         "/ST", dt.strftime("%H:%M"), "/SD", dt.strftime("%d/%m/%Y")],
        capture_output=True, text=True)
    if r.returncode == 0:
        return (f"lembrete agendado pra {dt.strftime('%d/%m/%Y às %H:%M')}, senhor: "
                f"“{mensagem.strip()}”. Aviso na tela na hora certa.")
    return f"o agendador do Windows recusou o lembrete: {r.stderr.strip()[:120]}"


def run(quando: str, mensagem: str) -> str:
    if not _WINDOWS:
        return ("lembretes na tela ainda só funcionam no Windows, senhor. "
                "Anotei o pedido: “" + mensagem.strip()[:60] + "”")
    dt = _interpretar_quando(quando)
    if dt is None:
        return (f"não entendi o momento “{quando}”. Tente '14:30', "
                "'em 20 minutos' ou '09/10/2026 08:00'.")
    return _agendar_windows(dt, mensagem)
