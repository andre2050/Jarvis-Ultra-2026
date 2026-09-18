"""HUD Ultra 2026 — holograma circular reativo, recolorível ao vivo.

O avatar do Ultra 2026 nasce como radar; a roadmap evolui pra cabeça
holográfica com dublagem (formantes). Tudo desenhado por software,
sem GPU. Cor da interface muda em tempo real com um hex.
"""
import math
import random
import time

import tkinter as tk


class Hud(tk.Canvas):
    def __init__(self, master, size: int = 340, **kw):
        if "bg" not in kw:
            try:
                kw["bg"] = master.cget("bg")
            except Exception:
                kw["bg"] = "#090d16"
        super().__init__(master, width=size, height=size,
                         highlightthickness=0, **kw)
        self.size = size
        self.cor = "#00e5c7"          # recolorível ao vivo
        self.energia = 0.0            # 0 dormindo .. 1 falando/ouvindo
        self._t0 = time.time()
        self._blips = [(random.random() * 2 * math.pi, random.uniform(0.3, 0.9)) for _ in range(7)]
        self._desenhar()
        self._animar()

    # ---------- estados ----------

    def pensando(self):    self.energia = 0.55
    def ouvindo(self):     self.energia = 1.0
    def falando(self):     self.energia = 0.85
    def dormindo(self):    self.energia = 0.12
    def recolorir(self, hexcor: str):
        self.cor = hexcor if hexcor.startswith("#") else self.cor
        self._desenhar()

    # ---------- desenho ----------

    def _desenhar(self):
        self.delete("all")
        s, cx, cy = self.size, self.size / 2, self.size / 2
        r = s * 0.40
        # glow radial (halos com alpha caindo)
        for dist, stip, w in ((1.14, "gray12", 9), (1.07, "gray25", 6), (1.02, "gray50", 3)):
            self.create_oval(cx - r * dist, cy - r * dist, cx + r * dist, cy + r * dist,
                             outline=self.cor, width=w, stipple=stip)
        # anéis concêntricos
        for fator in (1.0, 0.72, 0.45, 0.22):
            self.create_oval(cx - r * fator, cy - r * fator, cx + r * fator, cy + r * fator,
                            outline=self.cor, width=2 if fator == 1.0 else 1)
        # retículo (cross-hair)
        self.create_line(cx - r * 1.12, cy, cx + r * 1.12, cy, fill="#4384a5", width=1)
        self.create_line(cx, cy - r * 1.12, cx, cy + r * 1.12, fill="#4384a5", width=1)
        # núcleo
        self.nucleo = self.create_oval(cx - r * 0.16, cy - r * 0.16, cx + r * 0.16, cy + r * 0.16,
                                       fill=self.cor, outline="")
        # agulha de varredura + trilha (redesenhadas na animação)
        self.agulha = self.create_line(cx, cy, cx, cy, fill="#ff5a4d", width=2)
        self.trilha = self.create_arc(cx - r, cy - r, cx + r, cy + r, start=0, extent=0,
                                      style=tk.CHORD, fill=self.cor, stipple="gray25", outline="")
        # blips
        self.ids_blips = []
        for ang, dist in self._blips:
            bx = cx + r * dist * math.cos(ang)
            by = cy + r * dist * math.sin(ang)
            self.ids_blips.append(self.create_oval(bx - 2, by - 2, bx + 2, by + 2,
                                                   fill=self.cor, outline=""))
        # rótulos
        for ang, rotulo in ((-0.5, "ULTRA"), (0.9, "2026"), (2.6, "OLLAMA")):
            lx = cx + r * 1.24 * math.cos(ang)
            ly = cy + r * 1.24 * math.sin(ang)
            self.create_text(lx, ly, text=rotulo, fill="#8fb3c7",
                             font=("Consolas", 8, "bold"))

    def _animar(self):
        t = time.time() - self._t0
        s, cx, cy = self.size, self.size / 2, self.size / 2
        r = s * 0.40
        # agulha gira mais rápido conforme energia
        vel = 1.2 + self.energia * 3.5
        ang = math.radians((t * vel * 57.3) % 360)
        self.coords(self.agulha, cx, cy, cx + r * math.cos(ang), cy + r * math.sin(ang))
        self.itemconfig(self.trilha, start=math.degrees(ang) - 40, extent=40)
        # núcleo pulsa com a energia
        pulso = 0.16 * (1 + 0.18 * math.sin(t * (3 + self.energia * 7)))
        self.coords(self.nucleo, cx - r * pulso, cy - r * pulso, cx + r * pulso, cy + r * pulso)
        # blips cintilam
        for i, (bang, bdist) in enumerate(self._blips):
            alfa = 0.5 + 0.5 * math.sin(t * 2 + i * 2.1)
            if alfa > 0.25:
                bx = cx + r * bdist * math.cos(bang + t * 0.15)
                by = cy + r * bdist * math.sin(bang + t * 0.15)
                self.coords(self.ids_blips[i], bx - 2, by - 2, bx + 2, by + 2)
        self.after(50, self._animar)
