"""J.A.R.V.I.S — Ultra 2026 · desktop shell (v0.2.0 PRESENÇA).

Cérebro Ollama offline · avatar holográfico com dublagem real ·
push-to-talk Ctrl+Espaço · wake word "Ei, Jarvis" local · anti-eco ·
painel de memória · temática ao vivo · sessão que sobrevive a quedas.
Roadmap completo em docs/ROADMAP.md.
"""
import json
import queue
import sys
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

from core import config, ollama
from core.brain import Cerebro
from core.ouvido import Ouvido
from core.visemas import duracao_estimada
from core.voice import Voz
from ui.avatar import Avatar
from ui.hud import Hud
from ui.memoria import PainelMemoria
from version import APP_NAME, __version__

COR_FUNDO = "#090d16"
FRASE_TESTE = "Good evening. All systems are online and operating at full capacity."


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{__version__}")
        self.geometry("1080x720")
        self.minsize(900, 620)
        self.configure(bg=COR_FUNDO)

        self.cfg = config.load()
        self.voz = Voz(self.cfg)
        self.ouvido = Ouvido(self.cfg)
        self.cerebro = Cerebro(self.cfg)
        self.fila: queue.Queue = queue.Queue()
        self._ocupado = False
        self._ack_dado = False

        self._montar()
        self._ligar_escuta()
        self._carregar_sessao()
        self.after(600, self._checar_ambiente)
        self.after(80, self._consumir)
        self.after(1500, self._ack_instantaneo)
        self.protocol("WM_DELETE_WINDOW", self._sair)

    # ---------- interface ----------

    def _montar(self):
        corpo = tk.Frame(self, bg=COR_FUNDO)
        corpo.pack(fill=tk.BOTH, expand=True)

        esq = tk.Frame(corpo, bg=COR_FUNDO, width=400)
        esq.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 4), pady=10)
        esq.pack_propagate(False)

        # painel do rosto — avatar por padrão, radar a um clique
        self.moldura_rosto = tk.Frame(esq, bg=COR_FUNDO)
        self.moldura_rosto.pack(pady=(10, 4))
        self.avatar = Avatar(self.moldura_rosto, size=360,
                             bg=COR_FUNDO)
        self.avatar.pack()
        self.hud = Hud(self.moldura_rosto, size=360)
        self.hud.pack_forget()
        self.avatar.recolorir(self.cfg.get("cor", "#00e5c7"))
        self.hud.recolorir(self.cfg.get("cor", "#00e5c7"))

        barra_rosto = tk.Frame(esq, bg=COR_FUNDO)
        barra_rosto.pack(fill=tk.X, pady=(2, 6))
        tk.Button(barra_rosto, text="ROSTO ◄► RADAR", command=self._alternar_rosto,
                  bg="#0d121c", fg="#8fb3c7", bd=0, font=("Consolas", 8, "bold"),
                  cursor="hand2", padx=10, pady=5).pack()
        self.lbl_status = tk.Label(esq, text="inicializando…", font=("Consolas", 9),
                                   fg="#8fb3c7", bg=COR_FUNDO, wraplength=340,
                                   justify=tk.LEFT)
        self.lbl_status.pack(pady=(2, 6))

        # controles de presença
        pres = tk.Frame(esq, bg=COR_FUNDO)
        pres.pack(fill=tk.X, pady=(0, 10))
        self.btn_ptt = tk.Button(pres, text="🎙 SEGURE P/ FALAR\n(Ctrl+Espaço)",
                                 command=lambda: None, bg="#0d121c", fg="#00e5c7",
                                 bd=0, font=("Segoe UI", 9, "bold"), cursor="hand2",
                                 padx=8, pady=8, justify=tk.CENTER)
        self.btn_ptt.pack(fill=tk.X)
        self.btn_ptt.bind("<ButtonPress-1>", lambda e: self._ptt_segurar())
        self.btn_ptt.bind("<ButtonRelease-1>", lambda e: self.ouvido.soltar())
        self.btn_wake = tk.Button(pres, text='☾ WAKE WORD "EI, JARVIS"',
                                  command=self._alternar_wake, bg="#0d121c",
                                  fg="#8fb3c7", bd=0, font=("Segoe UI", 9, "bold"),
                                  cursor="hand2", padx=8, pady=8)
        self.btn_wake.pack(fill=tk.X, pady=(6, 0))
        tk.Button(pres, text="🧠 MEMÓRIA", command=self._abrir_memoria,
                  bg="#0d121c", fg="#8fb3c7", bd=0, font=("Segoe UI", 9, "bold"),
                  cursor="hand2", padx=8, pady=8).pack(fill=tk.X, pady=(6, 0))

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

    def _alternar_rosto(self):
        if self.avatar.winfo_ismapped():
            self.avatar.pack_forget()
            self.hud.pack()
        else:
            self.hud.pack_forget()
            self.avatar.pack()

    # ---------- escuta ----------

    def _ptt_segurar(self):
        """Apertou o microfone — se não dá pra escutar, avisa NA CARA."""
        ok, motivo = self.ouvido.estado()
        if not ok:
            messagebox.showinfo(
                "Microfone indisponível",
                f"{motivo}\n\nO chat continua funcionando por texto.")
            return
        self.ouvido.segurar()

    def _ligar_escuta(self):
        self.ouvido.on_frase = self._ouvir_texto
        self.ouvido.on_wake = self._acordado
        self.ouvido.on_estado = lambda msg: self.lbl_status.config(text=msg)

        def soltar_se_ativo():
            if self.ouvido.ptt_ativo():
                self.ouvido.soltar()

        # push-to-talk na janela (global com lib keyboard, se existir)
        self.bind("<Control-space>", lambda e: (self._ptt_segurar(), "break")[1])
        self.bind("<KeyRelease-space>", lambda e: soltar_se_ativo())
        if not self.ouvido.instalar_hotkey_global(self.ouvido.segurar, soltar_se_ativo):
            self.after(100, lambda: self.lbl_status.config(
                text="Ctrl+Espaço dentro da janela (global: pip install keyboard)"))

    def _ouvir_texto(self, texto: str):
        """Chegou fala do usuário — mesma fila do teclado (entrada híbrida)."""
        self.after(0, lambda: self._enviar(forcado=texto))

    def _acordado(self):
        def ao_acordar():
            self._falar_chat("Pois não, senhor?")
            self.avatar.ouvindo()
            self.ouvido.segurar()                 # abre o microfone pro comando
            self.after(6000, lambda: self.ouvido.ptt_ativo() and self.ouvido.soltar())
        self.after(0, ao_acordar)

    def _alternar_wake(self):
        ligado = self.ouvido.alternar_wake()
        self.btn_wake.config(text='☀ WAKE WORD LIGADO — "EI, JARVIS"' if ligado
                             else '☾ WAKE WORD "EI, JARVIS"',
                             fg="#00e5c7" if ligado else "#8fb3c7")

    def _abrir_memoria(self):
        PainelMemoria(self)

    # ---------- ambiente ----------

    def _checar_ambiente(self):
        ok_voz, motivo_voz = self.voz.estado()
        self.btn_voz.config(text=f"🎙 VOZ {'ON' if ok_voz else '—'}")
        self._falar_chat(f"Olá, {self.cfg.get('usuario', 'André')}. Ultra 2026 "
                         f"presença ativa — {len(self.cerebro.registro.nomes())} plugins: "
                         f"{', '.join(self.cerebro.registro.nomes())}.")
        if not ollama.disponivel(self.cfg.get("ollama_host")):
            self._falar_chat("aviso: servidor Ollama não responde — instale-o em ollama.com, "
                             "rode `ollama pull llama3.2` e volte. Até lá, penso mas não raciocino offline.")
        if not ok_voz:
            self._falar_chat(f"aviso de voz: {motivo_voz}")
        ok_ouvido, motivo_ouvido = self.ouvido.estado()
        if not ok_ouvido:
            self.lbl_status.config(text=f"escuta: {motivo_ouvido}")
        for err in self.cerebro.registro.erros:
            self._falar_chat(f"plugin com problema: {err[:120]}")
        self.avatar.dormindo()

    def _falar_chat(self, texto: str):
        self._add_chat("jarvis", texto)
        self.ouvido.anunciar_fala(texto)          # anti-eco: nunca respondo à minha voz
        self.avatar.falando(texto)                # dublagem: visemas do texto
        self.voz.falar(texto)
        vel = float(self.cfg.get("voz_velocidade", 0.85))
        self.after(int((duracao_estimada(texto, vel) + 1.2) * 1000),
                   self._adormecer_se_livre)

    def _adormecer_se_livre(self):
        if not self._ocupado and self.avatar.estado == "falando":
            self.avatar.dormindo()

    def _add_chat(self, quem: str, texto: str):
        cores = {"jarvis": "#00e5c7", "voce": "#c7d8e4", "erro": "#ff5a4d", "sys": "#8fb3c7"}
        cor = cores.get(quem, "#c7d8e4")
        self.chat.config(state=tk.NORMAL)
        self.chat.insert(tk.END, f"\n{'—' * 46}\n", cor)
        self.chat.insert(tk.END, f"{'JARVIS' if quem != 'voce' else 'VOCÊ'}  ", (cor,))
        self.chat.tag_config(cor, foreground=cor)
        self.chat.insert(tk.END, texto + "\n", cor)
        self.chat.see(tk.END)
        self.chat.config(state=tk.DISABLED)

    # ---------- conversa ----------

    def _enviar(self, forcado: str = None):
        texto = (forcado if forcado is not None else self.ent.get()).strip()
        if not texto or self._ocupado:
            return
        if forcado is None:
            self.ent.delete(0, tk.END)
        self._add_chat("voce", texto)
        self._ocupado = True
        self._ack_dado = False
        self.lbl_status.config(text="pensando…")
        self.avatar.pensando()

        def rodar():
            try:
                resposta = self.cerebro.responder(texto)
                self.fila.put(resposta)
            except Exception as e:
                self.fila.put(f"erro: {e}")

        threading.Thread(target=rodar, daemon=True).start()

    def _ack_instantaneo(self):
        """Confirmação instantânea: sem esperas silenciosas em tarefas longas."""
        if self._ocupado and not self._ack_dado:
            self._ack_dado = True
            self.lbl_status.config(text="processando, senhor…")
        self.after(1500, self._ack_instantaneo)

    def _consumir(self):
        try:
            while True:
                resposta = self.fila.get_nowait()
                self._ocupado = False
                self.lbl_status.config(text="pronto")
                self._falar_chat(resposta)
                self._salvar_sessao()
        except queue.Empty:
            pass
        self.after(80, self._consumir)

    # ---------- sessão contínua ----------

    def _carregar_sessao(self):
        """Uma queda de conexão ou um restart não apaga mais a conversa."""
        try:
            arq = config.CONFIG_DIR / "sessao.json"
            if arq.exists():
                hist = json.loads(arq.read_text(encoding="utf-8"))
                if hist:
                    self.cerebro.historico = hist
                    self._add_chat("sys", f"sessão anterior retomada — "
                                     f"{len(hist)} mensagens preservadas.")
        except Exception:
            pass

    def _salvar_sessao(self):
        try:
            config.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            (config.CONFIG_DIR / "sessao.json").write_text(
                json.dumps(self.cerebro.historico[-60:], ensure_ascii=False, indent=1),
                encoding="utf-8")
        except Exception:
            pass

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

        tk.Label(frame, text="VOZ DO SISTEMA", font=("Consolas", 9, "bold"),
                 fg="#8fb3c7", bg=COR_FUNDO).pack(anchor="w", pady=(10, 2))
        catalogo = list(self.voz.vozes) or [{"id": "", "nome": "automática"}]
        nomes = ["automática"] + [v["nome"] for v in catalogo]
        cmb_voz = ttk.Combobox(frame, values=nomes, width=30, state="readonly")
        atual = next((v["nome"] for v in catalogo if v["id"] == self.cfg.get("voz_id", "")), None)
        cmb_voz.set(atual or "automática")
        cmb_voz.pack(anchor="w")
        tk.Button(frame, text="testar voz", command=lambda: self.voz.falar(FRASE_TESTE),
                  bg="#0d121c", fg="#00e5c7", bd=0, font=("Segoe UI", 9, "bold"),
                  cursor="hand2", padx=10, pady=4).pack(anchor="w", pady=(4, 0))

        tk.Label(frame, text="MICROFONE", font=("Consolas", 9, "bold"),
                 fg="#8fb3c7", bg=COR_FUNDO).pack(anchor="w", pady=(10, 2))
        mics, _ = self.ouvido.dispositivos()
        cmb_mic = ttk.Combobox(frame, values=[n for _, n in mics] or ["padrão do sistema"],
                               width=30, state="readonly")
        cmb_mic.set(self.cfg.get("microfone", "") or "padrão do sistema")
        cmb_mic.pack(anchor="w")

        tk.Label(frame, text="COR DA INTERFACE (hex)", font=("Consolas", 9, "bold"),
                 fg="#8fb3c7", bg=COR_FUNDO).pack(anchor="w", pady=(10, 2))
        var_cor = tk.StringVar(value=self.cfg.get("cor", "#00e5c7"))
        tk.Entry(frame, textvariable=var_cor, width=33, bg="#0d121c",
                 fg="#c7d8e4", insertbackground="#00e5c7", bd=0).pack(anchor="w")

        tk.Label(frame, text="seu nome", font=("Consolas", 9, "bold"),
                 fg="#8fb3c7", bg=COR_FUNDO).pack(anchor="w", pady=(10, 2))
        var_nome = tk.StringVar(value=self.cfg.get("usuario", "André"))
        tk.Entry(frame, textvariable=var_nome, width=33, bg="#0d121c",
                 fg="#c7d8e4", insertbackground="#00e5c7", bd=0).pack(anchor="w")

        def salvar():
            self.cfg["ollama_model"] = cmb.get()
            nome_voz = cmb_voz.get()
            self.cfg["voz_id"] = next(
                (v["id"] for v in catalogo if v["nome"] == nome_voz), "")
            self.cfg["microfone"] = "" if cmb_mic.get() == "padrão do sistema" else cmb_mic.get()
            self.cfg["cor"] = var_cor.get().strip() or "#00e5c7"
            self.cfg["usuario"] = var_nome.get().strip() or "André"
            config.save(self.cfg)
            self.voz.reconfigurar()
            self.avatar.recolorir(self.cfg["cor"])
            self.hud.recolorir(self.cfg["cor"])
            j.destroy()

        tk.Button(frame, text="salvar", command=salvar, bg="#00e5c7", fg="#04211d",
                  bd=0, font=("Segoe UI", 9, "bold"), cursor="hand2",
                  padx=16, pady=6).pack(anchor="w", pady=(16, 0))

    def _sair(self):
        self.ouvido.desligar_wake()
        self._salvar_sessao()
        config.save(self.cfg)
        self.destroy()


def _garantir_voz():
    """Primeira execução: instala as libs de escuta faltando e relança."""
    import os
    from core import deps
    if os.environ.get("JARVIS_VOZ_TENTADA") == "1":
        return                      # já tentou nesta cadeia — não faz loop
    falta = deps.faltando()
    if not falta:
        return
    os.environ["JARVIS_VOZ_TENTADA"] = "1"
    janela = tk.Tk()
    janela.title("J.A.R.V.I.S — preparando a voz")
    janela.configure(bg="#090d16")
    lbl = tk.Label(janela, text="Instalando as bibliotecas de voz…\n(uma vez só, ~45 MB)",
                   font=("Segoe UI", 12), fg="#00e5c7", bg="#090d16", padx=30, pady=24)
    lbl.pack()
    janela.update()
    ok = deps.instalar([pip for pip, _ in falta],
                       ao_log=lambda m: (lbl.config(text=m + "\n(uma vez só)"), janela.update()))
    janela.destroy()
    if ok:
        os.execl(sys.executable, sys.executable, *sys.argv)
    # se falhou, o app segue — e avisa na cara na hora de usar o microfone


def main():
    try:
        _garantir_voz()
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
