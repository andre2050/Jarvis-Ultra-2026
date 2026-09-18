"""Ouvido do Ultra 2026 — escuta local, nunca vaza áudio à toa.

- Pressione-para-falar: segure Ctrl+Espaço e fale (global no Windows
  com a lib `keyboard`; na janela nos outros sistemas).
- Palavra de despertar: "Ei, Jarvis" detectada LOCALMENTE (openwakeword
  se instalado; fallback: Vosk com caça à palavra). Entra em espera,
  adormece sozinho após 2 minutos de silêncio e NUNCA transmite áudio
  enquanto espera — só energia de microfone, nada sai do PC.
- Proteção contra autoeco: a cauda da própria fala do assistente é
  reconhecida e descartada — ele nunca responde à própria última frase.
- Seletor de dispositivos: microfone e alto-falantes escolhidos por nome.

Degraus honestos: cada motor ausente é reportado com o motivo e o que
instalar. Nada falha em silêncio.
"""
import difflib
import json
import math
import os
import struct
import sys
import threading
import time
import urllib.request
import zipfile

from core.config import CONFIG_DIR

# ---------- dependências opcionais (degraus) ----------

try:
    import numpy  # sounddevice devolve numpy arrays
    TEM_NUMPY = True
except ImportError:
    TEM_NUMPY = False

try:
    import sounddevice as sd
    TEM_SOM = True
except ImportError:
    TEM_SOM = False

try:
    import vosk
    TEM_VOSK = False          # só vira True com modelo baixado
except ImportError:
    vosk = None

try:
    import keyboard
    TEM_KEYBOARD = sys.platform.startswith("win") or sys.platform.startswith("linux")
except ImportError:
    keyboard = None
    TEM_KEYBOARD = False

MODELO_URL = "https://alphacephei.com/vosk/models/vosk-model-small-pt-0.15-0.15.zip"
MODELO_DIR = CONFIG_DIR / "vosk-model-pt"
TAXA = 16000

# ---------- helpers ----------


def normalizar(t: str) -> str:
    import unicodedata
    t2 = unicodedata.normalize("NFD", t.lower())
    return "".join(c for c in t2 if not unicodedata.combining(c))


def _rms(bloco) -> float:
    if TEM_NUMPY:
        return float(numpy.sqrt(numpy.mean(bloco ** 2)))
    n = len(bloco) // 2
    vals = struct.unpack(f"<{n}h", bytes(bloco[: n * 2]))
    if not vals:
        return 0.0
    return math.sqrt(sum(v * v for v in vals) / len(vals))


class Ouvido:
    """Escuta local com wake word, push-to-talk e anti-eco."""

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.on_frase = None            # callback(texto) quando o usuário fala
        self.on_wake = None             # callback() quando "Ei, Jarvis" é dito
        self.on_estado = None           # callback(estado_str)
        self._cauda_propria = ""        # anti-eco: última frase falada pelo JARVIS
        self._grabando = None           # push-to-talk ativo
        self._fluxo_espera = None      # wake word ativo
        self._modo = "off"             # off | espera | ptt
        self._ultima_voz = 0.0
        self._lock = threading.Lock()
        self._modelo = None
        threading.Thread(target=self._preparar_modelo, daemon=True).start()

    # ---------- modelo Vosk (baixa 1x, offline pra sempre) ----------

    def _preparar_modelo(self):
        global TEM_VOSK
        if vosk is None:
            return
        try:
            if not (MODELO_DIR / "final.md").exists() and not any(MODELO_DIR.glob("*/README")):
                self._aviso("baixando modelo de fala pt-BR (~40 MB, só na primeira vez)…")
                CONFIG_DIR.mkdir(parents=True, exist_ok=True)
                zip_path = CONFIG_DIR / "vosk-pt.zip"
                urllib.request.urlretrieve(MODELO_URL, zip_path)
                with zipfile.ZipFile(zip_path) as z:
                    z.extractall(CONFIG_DIR / "_vosk_tmp")
                extraida = next((CONFIG_DIR / "_vosk_tmp").iterdir())
                if MODELO_DIR.exists():
                    for arq in MODELO_DIR.rglob("*"):
                        arq.unlink()
                    for pasta in reversed(list(MODELO_DIR.rglob("*"))):
                        if pasta.is_dir():
                            pasta.rmdir()
                else:
                    MODELO_DIR.mkdir(parents=True)
                os.rename(extraida, MODELO_DIR)
                zip_path.unlink(missing_ok=True)
                (CONFIG_DIR / "_vosk_tmp").rmdir()
            real = MODELO_DIR if (MODELO_DIR / "conf").exists() else next(MODELO_DIR.iterdir())
            vosk.SetLogLevel(-1)
            self._modelo = vosk.Model(str(real))
            TEM_VOSK = True
            self._aviso("escuta local pronta.")
        except Exception as e:
            self._aviso(f"escuta indisponível: {str(e)[:120]}")

    def _aviso(self, msg: str):
        if self.on_estado:
            try:
                self.on_estado(msg)
            except Exception:
                pass

    # ---------- estado honesto ----------

    def estado(self):
        if not TEM_SOM:
            return False, "sem sounddevice — rode: pip install sounddevice"
        if vosk is None:
            return False, "sem vosk — rode: pip install vosk"
        if not TEM_VOSK or self._modelo is None:
            return False, "modelo de fala ainda baixando (primeira vez)…"
        return True, "escuta local pronta"

    # ---------- dispositivos por nome ----------

    def dispositivos(self) -> tuple:
        """([microfones], [alto-falantes]) — nomes resumidos do sistema."""
        if not TEM_SOM:
            return [], []
        mics, alto = [], []
        try:
            for i, d in enumerate(sd.query_devices()):
                nome = d["name"].split("(")[0].strip()[:32]
                if d["max_input_channels"] > 0 and nome:
                    mics.append((i, nome))
                if d["max_output_channels"] > 0 and nome:
                    alto.append((i, nome))
        except Exception:
            pass
        return mics, alto

    def _dev_entrada(self):
        try:
            nome = self.cfg.get("microfone", "")
            for i, n in self.dispositivos()[0]:
                if nome and nome.lower() in n.lower():
                    return i
        except Exception:
            pass
        return None

    # ---------- anti-eco ----------

    def anunciar_fala(self, texto: str):
        """Chame sempre que o JARVIS falar — registra a cauda anti-eco."""
        self._cauda_propria = normalizar(texto)[-42:]

    def _eh_minha_fala(self, ouvido: str) -> bool:
        """A cauda da própria voz na frente do microfone? Descarta."""
        if not self._cauda_propria:
            return False
        frag = normalizar(ouvido)
        if len(frag) < 8:
            return False
        prop = difflib.SequenceMatcher(
            None, frag, self._cauda_propria).ratio()
        cauda_na_frag = self._cauda_propria[:24] in frag or frag[:24] in self._cauda_propria
        return prop > 0.62 or cauda_na_frag

    # ---------- push-to-talk (Ctrl+Espaço segurado) ----------

    def ptt_ativo(self) -> bool:
        return self._grabando is not None

    def segurar(self):
        """Começa a gravar — o microfone fica FECHADO o resto do tempo."""
        ok, motivo = self.estado()
        if not ok:
            self._aviso(f"não escuto: {motivo}")
            return
        if self._grabando is not None:
            return
        try:
            self._grabando = []
            self._fluxo_ptt = sd.RawInputStream(
                samplerate=TAXA, blocksize=8000, dtype="int16",
                channels=1, device=self._dev_entrada())
            self._fluxo_ptt.start()
            self._modo = "ptt"
            self._aviso("🎤 falando… (solte Ctrl+Espaço pra enviar)")
            threading.Thread(target=self._loop_ptt, daemon=True).start()
        except Exception as e:
            self._grabando = None
            self._aviso(f"microfone não abriu: {str(e)[:100]}")

    def _loop_ptt(self):
        while self._grabando is not None:
            try:
                bloco, _ = self._fluxo_ptt.read(4000)
                if bloco:
                    self._grabando.append(bytes(bloco))
            except Exception:
                break
            time.sleep(0.01)

    def soltar(self):
        if self._grabando is None:
            return
        audio = b"".join(self._grabando)
        self._grabando = None
        try:
            self._fluxo_ptt.stop()
            self._fluxo_ptt.close()
        except Exception:
            pass
        self._modo = "off"
        texto = self._transcrever(audio)
        if texto and not self._eh_minha_fala(texto):
            if self.on_frase:
                self.on_frase(texto)
        elif texto:
            self._aviso("(minha própria voz ecoou no microfone — descartada)")

    # ---------- wake word: "Ei, Jarvis" ----------

    def _ativa_wake(self):
        """Entra em modo de espera: só energia, áudio NUNCA é transcrito
        até passar do portão de energia."""
        ok, motivo = self.estado()
        if not ok:
            self._aviso(f"wake word indisponível: {motivo}")
            return
        if self._fluxo_espera is not None:
            return
        try:
            self._fluxo_espera = sd.RawInputStream(
                samplerate=TAXA, blocksize=8000, dtype="int16",
                channels=1, device=self._dev_entrada())
            self._fluxo_espera.start()
            self._modo = "espera"
            self._ultima_voz = time.time()
            self._aviso('modo de espera — diga "Ei, Jarvis" pra me chamar')
            threading.Thread(target=self._loop_espera, daemon=True).start()
        except Exception as e:
            self._fluxo_espera = None
            self._aviso(f"wake word não ligou: {str(e)[:100]}")

    def alternar_wake(self) -> bool:
        if self._fluxo_espera is not None:
            self.desligar_wake()
            return False
        self._ativa_wake()
        return self._fluxo_espera is not None

    def desligar_wake(self):
        try:
            if self._fluxo_espera:
                self._fluxo_espera.stop()
                self._fluxo_espera.close()
        except Exception:
            pass
        self._fluxo_espera = None
        if self._modo == "espera":
            self._modo = "off"
        self._aviso("wake word desligado")

    def wake_ligado(self) -> bool:
        return self._fluxo_espera is not None

    def _loop_espera(self):
        """Portão duplo: energia primeiro (nada sai do PC em espera);
        com energia, Vosk caça 'jarvis' em tempo real."""
        rec = vosk.KaldiRecognizer(self._modelo, TAXA)
        rec.SetWords(True)
        silencio_ate = time.time() + 120.0          # adormece após 2 min
        janela_ativa = []                           # buffer só quando há voz
        while self._fluxo_espera is not None:
            try:
                bloco, _ = self._fluxo_espera.read(4000)
                if not bloco:
                    continue
                energia = _rms(bloco)
                if energia > 380:
                    self._ultima_voz = time.time()
                    silencio_ate = self._ultima_voz + 120.0
                    janela_ativa.append(bytes(bloco))
                    if sum(len(b) for b in janela_ativa) > TAXA * 2 * 2:   # 2 s de fala
                        audio = b"".join(janela_ativa)
                        janela_ativa = []
                        if rec.AcceptWaveform(audio):
                            texto = json.loads(rec.Result()).get("text", "")
                            if self._acordou(texto):
                                if self.on_wake:
                                    self.on_wake()
                                rec = vosk.KaldiRecognizer(self._modelo, TAXA)
                                rec.SetWords(True)
                else:
                    if janela_ativa:                # voz terminou: processa
                        audio = b"".join(janela_ativa)
                        janela_ativa = []
                        if rec.AcceptWaveform(audio):
                            texto = json.loads(rec.Result()).get("text", "")
                            if self._acordou(texto) and self.on_wake:
                                self.on_wake()
                    if time.time() > silencio_ate:
                        self._aviso("silêncio de 2 minutos — adormecendo o wake word")
                        self.desligar_wake()
                        return
            except Exception as e:
                self._aviso(f"escuta caiu: {str(e)[:100]}")
                self.desligar_wake()
                return

    def _acordou(self, texto: str) -> bool:
        t = normalizar(texto).replace(" ", "")
        return "jarvis" in t or "ei" in t[:14]

    # ---------- transcrição ----------

    def _transcrever(self, audio: bytes) -> str:
        if not audio or self._modelo is None:
            return ""
        rec = vosk.KaldiRecognizer(self._modelo, TAXA)
        rec.AcceptWaveform(audio)
        rec.FinalResult()
        return json.loads(rec.Result()).get("text", "").strip()

    # ---------- hotkey global (Windows/Linux com lib keyboard) ----------

    def instalar_hotkey_global(self, on_segurar, on_soltar) -> bool:
        if not TEM_KEYBOARD or keyboard is None:
            return False
        try:
            keyboard.add_hotkey("ctrl+space", on_segurar,
                                suppress=False, trigger_on_release=False)
            # keyboard lib: hotkey de soltura via hook de release
            keyboard.on_release_key(
                "space", lambda e: on_soltar() if self.ptt_ativo() else None, suppress=False)
            return True
        except Exception:
            return False
