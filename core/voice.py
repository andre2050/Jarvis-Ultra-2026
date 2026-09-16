"""Voz do Ultra 2026 — cadeia de motores, NUNCA fica mudo.

  1. pyttsx3 (vozes do sistema, seletor, velocidade)
  2. TTS NATIVO do Windows via PowerShell (zero dependências)

Lição gravada do projeto anterior: qualquer falha num único motor
não pode significar silêncio. O texto sempre entra na fila; o loop
decide qual motor fala.
"""
import queue
import subprocess
import sys
import threading

try:
    import pyttsx3
    TEM_PYTTSX3 = True
except ImportError:
    TEM_PYTTSX3 = False


def _tts_powershell(texto: str, velocidade: float, volume: float) -> tuple:
    """TTS nativo do Windows — funciona em qualquer Windows, sem instalar nada."""
    if not sys.platform.startswith("win"):
        return False, "voz nativa só no Windows"
    try:
        rate = max(-10, min(10, int(round((velocidade - 1.0) * 10))))
        vol = max(0, min(100, int(volume * 100)))
        esc = (texto.replace("'", "''").replace("\r", " ").replace("\n", " "))[:800]
        cmd = ("Add-Type -AssemblyName System.Speech;"
               "$j = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
               f"$j.Rate = {rate}; $j.Volume = {vol};"
               f"$j.Speak('{esc}')")
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy",
                        "Bypass", "-Command", cmd], timeout=60,
                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, creationflags=flags, check=False)
        return True, ""
    except Exception as e:
        return False, str(e)


class Voz:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = bool(config.get("voz_ativa", True))
        self._fila: queue.Queue = queue.Queue()
        self._status = "iniciando"   # ok | sem_biblioteca | erro_engine | sem_voz
        self._erro = ""
        self._ps_ok = None           # sonda do TTS nativo (cacheada)
        self.vozes = []              # catálogo para o seletor
        threading.Thread(target=self._loop, daemon=True).start()

    # ---------- API ----------

    def falar(self, texto: str) -> None:
        if not self.enabled:
            return
        limpo = texto.replace("**", "").replace("##", "").replace("`", "").strip()
        if limpo:
            self._fila.put(limpo)

    def alternar(self) -> bool:
        self.enabled = not self.enabled
        self.config["voz_ativa"] = self.enabled
        return self.enabled

    def reconfigurar(self) -> None:
        """Reaplica config no engine em uso (voz escolhida/velocidade) — na hora."""
        self._fila.put("__reconfigurar__")

    def estado(self) -> tuple:
        """(pode_falar, motivo) — diagnóstico honesto."""
        if self._status == "ok":
            return True, "ok"
        if self._status == "iniciando" and not TEM_PYTTSX3:
            self._status = "sem_biblioteca"
        if self._status == "iniciando":
            return False, "motor inicializando…"
        motivo_py = ("pyttsx3 não instalado" if self._status == "sem_biblioteca"
                     else f"pyttsx3 falhou: {self._erro[:120]}")
        if self._ps_ok is None:
            self._ps_ok = _probe_powershell()
        if self._ps_ok:
            return True, f"falando pela VOZ NATIVA DO WINDOWS ({motivo_py})"
        return False, f"nenhum motor funciona ({motivo_py} | nativo indisponível)"

    # ---------- engine ----------

    def _loop(self) -> None:
        if not TEM_PYTTSX3:
            self._status = "sem_biblioteca"
        engine = None
        if TEM_PYTTSX3:
            try:
                engine = pyttsx3.init()
                self._configurar(engine)
                self._status, self._erro = "ok", ""
            except Exception as e:
                engine = None
                self._status, self._erro = "erro_engine", str(e)
        while True:
            texto = self._fila.get()
            if texto == "__reconfigurar__":
                if engine is not None:
                    self._configurar(engine)
                continue
            falou = False
            if engine is None and TEM_PYTTSX3:
                try:
                    engine = pyttsx3.init()
                    self._configurar(engine)
                    self._status, self._erro = "ok", ""
                except Exception as e:
                    engine = None
                    self._status, self._erro = "erro_engine", str(e)
            if engine is not None:
                try:
                    engine.say(texto)
                    engine.runAndWait()
                    falou = True
                except Exception as e:
                    self._status, self._erro = "erro_engine", str(e)
                    try:
                        engine = pyttsx3.init()
                        self._configurar(engine)
                    except Exception:
                        engine = None
            if not falou:
                ok_ps, err_ps = _tts_powershell(
                    texto, float(self.config.get("voz_velocidade", 0.85)),
                    float(self.config.get("voz_volume", 1.0)))
                if ok_ps:
                    self._ps_ok = True
                else:
                    self._ps_ok = False
                    self._status = "sem_voz"
                    self._erro = f"pyttsx3: {self._erro[:80]} | nativo: {err_ps[:80]}"

    def _configurar(self, engine) -> None:
        try:
            rate = int(engine.getProperty("rate"))
            engine.setProperty("rate", int(rate * float(self.config.get("voz_velocidade", 0.85))))
            engine.setProperty("volume", float(self.config.get("voz_volume", 1.0)))
            try:
                disponiveis = list(engine.getProperty("voices") or [])
                self.vozes = [{"id": getattr(v, "id", str(i)),
                               "nome": v.name or f"voz {i+1}"} for i, v in enumerate(disponiveis)]
            except Exception:
                disponiveis = []
            escolhida = (self.config.get("voz_id") or "").strip()
            if escolhida:
                for v in disponiveis:
                    if getattr(v, "id", "") == escolhida:
                        engine.setProperty("voice", escolhida)
                        return
            preferidas = []
            for v in disponiveis:
                nome = (v.name or "").lower()
                idioma = (getattr(v, "id", "") or "").lower() + " " + nome
                if "pt" in idioma and ("male" in nome or "felipe" in nome or "daniel" in nome):
                    preferidas.insert(0, v)
                elif "en-gb" in idioma or "daniel" in nome or "george" in nome:
                    preferidas.append(v)
            if preferidas:
                engine.setProperty("voice", preferidas[0].id)
        except Exception:
            pass


def _probe_powershell() -> bool:
    """Sonda: System.Speech responde nesse Windows?"""
    if not sys.platform.startswith("win"):
        return False
    try:
        cmd = ("Add-Type -AssemblyName System.Speech;"
               "$j = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
               "$j.GetInstalledVoices().Count | Out-Null")
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        r = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy",
                            "Bypass", "-Command", cmd], timeout=25,
                           stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, creationflags=flags, check=False)
        return r.returncode == 0
    except Exception:
        return False
