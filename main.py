"""J.A.R.V.I.S — Ultra 2026 · desktop shell.

Fundação: cérebro Ollama offline, plugins auto-descritivos, voz à prova
de mudo, HUD reativo recolorível, memória persistente. Roadmap completo
em docs/ROADMAP.md (web, celular, avatar com dublagem).
"""
import queue
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

from core import config, ollama
from core.brain import Cerebro
from core.voice import Voz
from ui.hud import Hud
from version import APP_NAME, __version__

COR_FUNDO = "#090d16"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{__version__}")
        self.geometry("1080x720")
        self.minsize(900, 620)
        self.configure(bg=COR_FUNDO)

        self.cfg = config.load()
        self.voz = Voz(self.cfg)
        self.cerebro = Cerebro(self.cfg)
        self.fila: queue.Queue = queue.Queue()
        self._ocupado = False

        self._montar()
        self.after(600, self._checar_ambiente)
        self.after(80, self._consumir)
        self.protocol("WM_DELETE_WINDOW", self._sair)

    # ---------- interface ----------

    def _montar(self):
        corpo = tk.Frame(self, bg=COR_FUNDO)
        corpo.pack(fill=tk.BOTH, expand=True)

        esq = tk.Frame(corpo, bg=COR_FUNDO, width=380)
        esq.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 4), pady=10)
        esq.pack_propagate(False)
        self.hud = Hud(esq, size=360)
        self.hud.pack(pady=(10, 4))
        self.lbl_status = tk.Label(esq, text="inicializando…", font=("Consolas", 9),
                                   fg="#8fb3c7", bg=COR_FUNDO)
        self.lbl_status.pack(pady=(2, 10))

        dir_ = tk.Frame(corpo, bg=COR_FUNDO)
        dir_.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 10), pady=10)
        self.chat = scrolledtext.ScrolledText(
            dir_, bg="#0d121c", fg="#c7d8e4", insertbackground="#00e5c7",
            font=("Segoe UI", 10), bd=0, wrap=tk.WORD, state=tk.DISABLED)
        self.chat.pack(fill=tk.BOTH, expand=True)

        barra = tk.Frame(dir_, bg=COR_FUNDO)
        barra.pack(fill=tk.X, pady=(8, 0))
        self.ent = tk.Entry(barra, bg="#0d121c", fg="#c7d8e4", insertbackground="#00e5c7",
                            font=("Segoe UI", 11), bd=0)
        self.ent.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 8))
        self.ent.bind("<Return>", lambda e: self._enviar())
        tk.Button(barra, text="ENVIAR", command=self._enviar, bg="#00e5c7", fg="#04211d",
                  bd=0, font=("Segoe UI", 9, "bold"), cursor="hand2",
                  padx=14, pady=8).pack(side=tk.LEFT)
        tk.Button(barra, text="⚙", command=self._config,
                  bg="#0d121c", fg="#8fb3c7", bd=0, font=("Segoe UI", 11), cursor="hand2",
                  padx=10, pady=8).pack(side=tk.RIGHT)
        self.btn_voz = tk.Button(barra, text="🎙 VOZ ON", command=self._alternar_voz,
                                 bg="#0d121c", fg="#00e5c7", bd=0, font=("Segoe UI", 9, "bold"),
                                 cursor="hand2", padx=10, pady=8)
        self.btn_voz.pack(side=tk.RIGHT, padx=(0, 8))
        self.ent.focus_set()

    # ---------- ambiente ----------

    def _checar_ambiente(self):
        ok_voz, motivo_voz = self.voz.estado()
        self.btn_voz.config(text=f"🎙 VOZ {'ON' if ok_voz else '—'}")
        self._falar_chat(f"Olá, André. Ultra 2026 online — {len(self.cerebro.registro.nomes())} "
                         f"plugins carregados: {', '.join(self.cerebro.registro.nomes())}.")
        if not ollama.disponivel(self.cfg.get("ollama_host")):
            self._falar_chat("aviso: servidor Ollama não responde — instale-o em ollama.com, "
                             "rode `ollama pull llama3.2` e volte. Até lá, penso mas não raciocino offline.")
        if not ok_voz:
            self._falar_chat(f"aviso de voz: {motivo_voz}")
        for err in self.cerebro.registro.erros:
            self._falar_chat(f"plugin com problema: {err[:120]}")
        self.hud.dormindo()

    def _falar_chat(self, texto: str):
        self._add_chat("jarvis", texto)
        self.voz.falar(texto)

    def _add_chat(self, quem: str, texto: str):
        cores = {"jarvis": "#00e5c7", "voce": "#c7d8e4", "erro": "#ff5a4d", "sys": "#8fb3c7"}
        self.chat.config(state=tk.NORMAL)
        self.chat.insert(tk.END, f"\n{'—' * 46}\n", cores.get(quem, "#c7d8e4"))
        self.chat.insert(tk.END, f"{'JARVIS' if quem != 'voce' else 'VOCÊ'}  ", (cores.get(quem, "#c7d8e4"),))
        self.chat.tag_config(cores.get(quem, "#c7d8e4"), foreground=cores.get(quem, "#c7d8e4"))
        self.chat.insert(tk.END, texto + "\n", cores.get(quem, "#c7d8e4"))
        self.chat.see(tk.END)
        self.chat.config(state=tk.DISABLED)

    # ---------- conversa ----------

    def _enviar(self):
        texto = self.ent.get().strip()
        if not texto or self._ocupado:
            return
        self.ent.delete(0, tk.END)
        self._add_chat("voce", texto)
        self._ocupado = True
        self.lbl_status.config(text="pensando…")
        self.hud.pensando()

        def rodar():
            try:
                resposta = self.cerebro.responder(texto)
                self.fila.put(resposta)
            except Exception as e:
                self.fila.put(f"erro: {e}")

        threading.Thread(target=rodar, daemon=True).start()

    def _consumir(self):
        try:
            while True:
                resposta = self.fila.get_nowait()
                self._ocupado = False
                self.lbl_status.config(text="pronto")
                self.hud.falando()
                self._falar_chat(resposta)
                self.after(4000, self.hud.dormindo)
        except queue.Empty:
            pass
        self.after(80, self._consumir)

    # ---------- controles ----------

    def _alternar_voz(self):
        ligado = self.voz.alternar()
        config.save(self.cfg)
        self.btn_voz.config(text=f"🎙 VOZ {'ON' if ligado else 'OFF'}",
                            fg="#00e5c7" if ligado else "#5a6a76")
        if not ligado:
            self._add_chat("sys", "voz desativada")

    def _config(self):
        j = tk.Toplevel(self)
        j.title("CONFIG — Ultra 2026")
        j.configure(bg=COR_FUNDO)
        j.transient(self)
        frame = tk.Frame(j, bg=COR_FUNDO, padx=24, pady=18)
        frame.pack()
        tk.Label(frame, text="MODELO OLLAMA", font=("Consolas", 9, "bold"),
                 fg="#8fb3c7", bg=COR_FUNDO).pack(anchor="w", pady=(0, 2))
        modelos = ollama.modelos(self.cfg.get("ollama_host")) or ["llama3.2"]
        cmb = ttk.Combobox(frame, values=modelos, width=30, state="readonly")
        cmb.set(self.cfg.get("ollama_model", "llama3.2"))
        cmb.pack(anchor="w")
        tk.Label(frame, text="COR DO HUD (hex)", font=("Consolas", 9, "bold"),
                 fg="#8fb3c7", bg=COR_FUNDO).pack(anchor="w", pady=(10, 2))
        var_cor = tk.StringVar(value=self.cfg.get("cor", "#00e5c7"))
        ent_cor = tk.Entry(frame, textvariable=var_cor, width=33, bg="#0d121c",
                           fg="#c7d8e4", insertbackground="#00e5c7", bd=0)
        ent_cor.pack(anchor="w")
        tk.Label(frame, text="seu nome", font=("Consolas", 9, "bold"),
                 fg="#8fb3c7", bg=COR_FUNDO).pack(anchor="w", pady=(10, 2))
        var_nome = tk.StringVar(value=self.cfg.get("usuario", "André"))
        tk.Entry(frame, textvariable=var_nome, width=33, bg="#0d121c",
                 fg="#c7d8e4", insertbackground="#00e5c7", bd=0).pack(anchor="w")

        def salvar():
            self.cfg["ollama_model"] = cmb.get()
            self.cfg["cor"] = var_cor.get().strip() or "#00e5c7"
            self.cfg["usuario"] = var_nome.get().strip() or "André"
            config.save(self.cfg)
            self.hud.recolorir(self.cfg["cor"])
            j.destroy()

        tk.Button(frame, text="salvar", command=salvar, bg="#00e5c7", fg="#04211d",
                  bd=0, font=("Segoe UI", 9, "bold"), cursor="hand2",
                  padx=16, pady=6).pack(anchor="w", pady=(16, 0))

    def _sair(self):
        config.save(self.cfg)
        self.destroy()


def main():
    try:
        App().mainloop()
    except Exception:
        import traceback
        from core.config import CONFIG_DIR
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        (CONFIG_DIR / "erro.log").write_text(traceback.format_exc(), encoding="utf-8")
        try:
            messagebox.showerror("Ultra 2026", "Falha ao iniciar — detalhes em erro.log")
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()
