"""Avatar holográfico — uma cabeça humana animada no HUD.

Geometria facial real desenhada por software (tkinter canvas), sem
GPU e sem pacotes extras: crânio, mandíbula, olhos com pálpebras,
pupilas que se movem entre fixações, sobrancelhas, nariz e boca
que se articula em ~50 formas por segundo a partir dos visemas.

Atuação: sobrancelhas acompanham a frase, piscadas naturais, leve
aceno de cabeça nas tônicas. Rosto como status: desvia o olhar
pensando, encontra seu olhar ouvindo, pálpebras caem dormindo.
Recolorível ao vivo por hex — o avatar acompanha a interface.
"""
import math
import random
import time

from core import visemas

# formas de boca: (largura_px, abertura_px, arredondamento 0..1, canto_sobe -1..1)
FORMAS = {
    "MM": (56, 1.5, 0.0, 0.0),
    "AA": (52, 22.0, 0.15, -0.1),
    "EH": (60, 13.0, 0.05, 0.1),
    "IH": (62, 6.0, 0.0, 0.25),
    "OH": (34, 18.0, 0.85, 0.0),
    "UH": (28, 9.0, 0.9, 0.0),
    "FF": (54, 4.0, 0.1, 0.15),
    "SS": (40, 2.5, 0.0, 0.2),
}


import tkinter as tk


class Avatar(tk.Canvas):
    """Cabeça holográfica. Estados: pensando/ouvindo/falando/dormindo."""

    def __init__(self, master, size: int = 360, **kw):
        if "bg" not in kw:
            try:
                kw["bg"] = master.cget("bg")
            except Exception:
                kw["bg"] = "#090d16"
        super().__init__(master, width=size, height=size,
                         highlightthickness=0, **kw)
        self.size = size
        self.cor = "#00e5c7"
        self.estado = "dormindo"        # pensando | ouvindo | falando | dormindo
        self.energia = 0.12
        # boca
        self._agenda: list = []         # [(visema, até_timestamp), ...]
        self._boca = dict(lar=56.0, abe=1.5, arr=0.0, cor=0.0)   # valores atuais (interp)
        self._boca_alvo = (56.0, 1.5, 0.0, 0.0)
        # olhos
        self._pupila = [0.0, 0.0]       # posição relativa atual
        self._fixacao = (0.0, 0.0)      # alvo do olhar
        self._prox_sacada = time.time() + 1.0
        self._palpebra = 0.0            # 0 aberto .. 1 fechado
        self._palpebra_alvo = 0.0
        self._prox_piscada = time.time() + random.uniform(2.5, 6.0)
        self._piscando = 0.0
        # sobrancelhas / aceno
        self._sobr = 0.0                # -1 caída .. 1 erguida
        self._sobr_alvo = 0.0
        self._aceno = 0.0
        self._t0 = time.time()
        self._ids: dict = {}
        self._montar()
        self._animar()

    # ---------- estados ----------

    def pensando(self):
        self.estado, self.energia = "pensando", 0.55
        self._fixacao = (-0.55, -0.45)          # desvia o olhar
        self._sobr_alvo = 0.35
        self._agenda = []

    def ouvindo(self):
        self.estado, self.energia = "ouvindo", 1.0
        self._fixacao = (0.0, 0.0)              # encontra seu olhar
        self._sobr_alvo = 0.55
        self._agenda = []

    def falando(self, texto: str = ""):
        """Agenda as formas de boca a partir do texto (dublagem)."""
        self.estado, self.energia = "falando", 0.85
        self._fixacao = (0.0, 0.05)
        self._sobr_alvo = 0.45
        if texto:
            t = time.time() + 0.15
            self._agenda = []
            for visema, dur in visemas.frase_para_visemas(
                    texto, 0.85):
                self._agenda.append((visema, t))
                t += dur
            self._agenda.append(("MM", t + 0.3))

    def dormindo(self):
        self.estado, self.energia = "dormindo", 0.12
        self._fixacao = (0.0, 0.15)
        self._sobr_alvo = -0.3
        self._palpebra_alvo = 0.72              # pálpebras caem
        self._agenda = []
        self.after(300, lambda: self._se_dormindo_palpebra())

    def _se_dormindo_palpebra(self):
        if self.estado != "dormindo":
            self._palpebra_alvo = 0.0

    def recolorir(self, hexcor: str):
        if hexcor.startswith("#") and len(hexcor) == 7:
            self.cor = hexcor

    # ---------- montagem (ids fixos, coords mudam na animação) ----------

    def _montar(self):
        self.delete("all")
        s = self.size
        cx, cy = s / 2, s * 0.52
        self.cx, self.cy = cx, cy
        rx, ry = s * 0.255, s * 0.315
        self.rx, self.ry = rx, ry
        ids = self._ids
        # halos do crânio (glow radial por stipple)
        ids["halo1"] = self.create_oval(cx - rx * 1.18, cy - ry * 1.14, cx + rx * 1.18, cy + ry * 1.12,
                                        outline=self.cor, width=8, stipple="gray12")
        ids["halo2"] = self.create_oval(cx - rx * 1.10, cy - ry * 1.08, cx + rx * 1.10, cy + ry * 1.06,
                                        outline=self.cor, width=5, stipple="gray25")
        # crânio
        ids["cranio"] = self.create_oval(cx - rx, cy - ry, cx + rx, cy + ry,
                                         outline=self.cor, width=2)
        # linha de cabelo (arco superior interno)
        ids["cabelo"] = self.create_arc(cx - rx * 0.92, cy - ry * 0.92, cx + rx * 0.92, cy + ry * 0.35,
                                        start=20, extent=140, style=tk.ARC,
                                        outline=self.cor, width=1.5)
        # mandíbula
        ids["mandibula"] = self.create_arc(cx - rx * 0.78, cy - ry * 0.1, cx + rx * 0.78, cy + ry * 1.45,
                                           start=210, extent=120, style=tk.ARC,
                                           outline=self.cor, width=1.5)
        # linhas de holograma (varreduras horizontais)
        ids["scan"] = []
        for fy in (-0.62, -0.3, 0.05, 0.42, 0.75):
            meia_largura = rx * math.sqrt(max(0.0, 1 - min(1.0, abs(fy)) ** 2 * 0.55))
            ids["scan"].append(self.create_line(
                cx - meia_largura, cy + ry * fy, cx + meia_largura, cy + ry * fy,
                fill=self.cor, width=1, stipple="gray25"))
        # nariz
        ids["nariz"] = self.create_line(cx - 7, cy + ry * 0.08, cx, cy + ry * 0.22,
                                        cx + 7, cy + ry * 0.08, smooth=True,
                                        fill=self.cor, width=1.5)
        # olhos (âineis externos, pupilas, pálpebras)
        ids["olhos"], ids["pupilas"], ids["palpebras"] = [], [], []
        for lado in (-1, 1):
            ex = cx + lado * rx * 0.40
            ey = cy - ry * 0.18
            ids["olhos"].append(self.create_oval(ex - 15, ey - 8, ex + 15, ey + 8,
                                                 outline=self.cor, width=1.5))
            ids["pupilas"].append(self.create_oval(ex - 4.5, ey - 4.5, ex + 4.5, ey + 4.5,
                                                  fill=self.cor, outline=""))
            ids["palpebras"].append(self.create_oval(ex - 16, ey - 9, ex + 16, ey + 9,
                                                     fill=self._bg(), outline=""))
        # sobrancelhas
        ids["sobrs"] = []
        for lado in (-1, 1):
            ex = cx + lado * rx * 0.40
            ids["sobrs"].append(self.create_line(ex - 16, 0, ex + 16, 0,
                                                 fill=self.cor, width=3, capstyle="round"))
        # boca (linha suave — coords mudam por visema)
        ids["boca"] = self.create_line(cx - 28, cy + ry * 0.55, cx, cy + ry * 0.55,
                                       cx + 28, cy + ry * 0.55, smooth=True,
                                       fill=self.cor, width=3, capstyle="round")
        # retículo discreto atrás
        ids["eixo_h"] = self.create_line(cx - s * 0.46, cy, cx + s * 0.46, cy,
                                         fill="#4384a5", width=1)
        ids["eixo_v"] = self.create_line(cx, cy - s * 0.46, cx, cy + s * 0.46,
                                         fill="#4384a5", width=1)
        self.tag_lower("eixo_h")
        self.tag_lower("eixo_v")

    def _bg(self):
        try:
            return self["bg"]
        except Exception:
            return "#090d16"

    # ---------- animação ----------

    def _animar(self):
        t = time.time() - self._t0
        agora = time.time()
        ids = self._ids
        cx, cy, rx, ry = self.cx, self.cy, self.rx, self.ry

        # -- boca: consome a agenda e interpola (~40-50 formas/s) --
        while self._agenda and self._agenda[0][1] <= agora:
            visema = self._agenda.pop(0)[0]
            self._boca_alvo = FORMAS.get(visema, FORMAS["MM"])
            # aceno leve nas tônicas (visemas abertos)
            if visema in ("AA", "EH", "OH"):
                self._aceno = 1.0
        if not self._agenda and self.estado != "falando":
            self._boca_alvo = FORMAS["MM"]
        k = 0.45
        b = self._boca
        alvo = self._boca_alvo
        b["lar"] += (alvo[0] - b["lar"]) * k
        b["abe"] += (alvo[1] - b["abe"]) * k
        b["arr"] += (alvo[2] - b["arr"]) * k
        b["cor"] += (alvo[3] - b["cor"]) * k
        # desenha a boca: curva superior + curva inferior pela abertura
        my = cy + ry * 0.55 + math.sin(t * 0.8) * 0.6 * self._aceno
        half = b["lar"] / 2
        sup = my - b["abe"] * (0.30 + 0.10 * b["cor"])
        inf = my + b["abe"]
        corner_up = -b["cor"] * 4
        if b["arr"] > 0.5:                             # arredondada (OH/UH)
            self.coords(ids["boca"], cx - half, my - b["cor"] * 4, cx - half * 0.5, sup,
                        cx, sup, cx + half * 0.5, sup, cx + half, my - b["cor"] * 4,
                        cx + half * 0.55, inf, cx, inf + b["abe"] * 0.35,
                        cx - half * 0.55, inf)
        else:
            self.coords(ids["boca"], cx - half, my + corner_up, cx - half * 0.45, sup,
                        cx + half * 0.45, sup, cx + half, my + corner_up,
                        cx + half * 0.40, inf, cx, inf + b["abe"] * 0.25,
                        cx - half * 0.40, inf)
        self._aceno *= 0.82

        # -- olhar: sacadas entre fixações --
        if agora > self._prox_sacada:
            if self.estado == "pensando":
                self._fixacao = (random.uniform(-0.7, -0.2), random.uniform(-0.6, 0.2))
            elif self.estado == "ouvindo":
                self._fixacao = (random.uniform(-0.12, 0.12), random.uniform(-0.1, 0.12))
            else:
                self._fixacao = (random.uniform(-0.15, 0.15), random.uniform(-0.05, 0.1))
            self._prox_sacada = agora + random.uniform(0.7, 2.2)
        kp = 0.18
        self._pupila[0] += (self._fixacao[0] * 6 - self._pupila[0]) * kp
        self._pupila[1] += (self._fixacao[1] * 5 - self._pupila[1]) * kp

        # -- piscadas naturais --
        if agora > self._prox_piscada and self.estado != "dormindo":
            self._piscando = agora + 0.13
            self._prox_piscada = agora + random.uniform(2.5, 7.0)
        alvo_palpebra = self._palpebra_alvo
        if agora < self._piscando:
            alvo_palpebra = max(alvo_palpebra, 0.95)
        self._palpebra += (alvo_palpebra - self._palpebra) * 0.5

        # -- sobrancelhas --
        self._sobr += (self._sobr_alvo - self._sobr) * 0.2
        sobr_y = cy - ry * 0.18 - 14 - self._sobr * 7 + math.sin(t * 3.1) * 1.2 * self._aceno

        # -- aceno de cabeça (translação vertical suave) --
        nod = math.sin(t * 2.2) * 1.8 * self._aceno

        for i, lado in enumerate((-1, 1)):
            ex = cx + lado * rx * 0.40
            ey = cy - ry * 0.18 + nod
            self.coords(ids["olhos"][i], ex - 15, ey - 8, ex + 15, ey + 8)
            px, py = ex + self._pupila[0], ey + self._pupila[1]
            self.coords(ids["pupilas"][i], px - 4.5, py - 4.5, px + 4.5, py + 4.5)
            # pálpebra: oval de fundo que desce cobrindo o olho
            altura_aberta = 18 * (1 - min(1.0, self._palpebra))
            py_top = ey - 9
            self.coords(ids["palpebras"][i], ex - 16, py_top,
                        ex + 16, py_top + (18 - altura_aberta) + 9)
            self.tag_raise(ids["pupilas"][i])
            self.tag_lower(ids["palpebras"][i], ids["nariz"])
            sy = sobr_y + nod
            incl = lado * (0.06 + self._sobr * 0.02)
            self.coords(ids["sobrs"][i], ex - 16, sy + incl * 16, ex + 16, sy - incl * 16)

        # -- energia: halo do crânio respira --
        pulso = 1.16 + 0.02 * math.sin(t * (1.5 + self.energia * 4))
        self.coords(ids["halo1"], cx - rx * pulso, cy - ry * pulso, cx + rx * pulso, cy + ry * pulso)
        for item in ("halo1", "halo2", "cranio", "cabelo", "mandibula", "nariz", "boca"):
            try:
                self.itemconfig(ids[item], outline=self.cor)
            except Exception:
                pass
        for sub in ("pupilas", "sobrs"):
            for pid in ids[sub]:
                try:
                    self.itemconfig(pid, fill=self.cor)
                except Exception:
                    pass
        self.after(25, self._animar)          # 40 fps ≈ 50 formas de boca/s interpoladas
