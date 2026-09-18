"""Painel de memória — tudo que o JARVIS sabe sobre você, às claras.

Veja cada informação memorizada, QUANDO foi aprendida, busque por
palavra e apague qualquer uma com um clique. Transparência total.
"""
import tkinter as tk
from tkinter import ttk

from core import memory


class PainelMemoria(tk.Toplevel):
    def __init__(self, master, ao_apagar=None):
        super().__init__(master)
        self.title("MEMÓRIA — o que eu sei de você")
        self.configure(bg="#090d16")
        self.transient(master)
        self.geometry("640x520")
        self.ao_apagar = ao_apagar
        self._montar()
        self._listar()

    def _montar(self):
        topo = tk.Frame(self, bg="#090d16")
        topo.pack(fill=tk.X, padx=16, pady=(14, 4))
        tk.Label(topo, text="🔍", font=("Segoe UI", 11), bg="#090d16",
                 fg="#00e5c7").pack(side=tk.LEFT)
        self.var_busca = tk.StringVar()
        ent = tk.Entry(topo, textvariable=self.var_busca, bg="#0d121c",
                       fg="#c7d8e4", insertbackground="#00e5c7", bd=0,
                       font=("Segoe UI", 10))
        ent.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=8)
        ent.bind("<KeyRelease>", lambda e: self._listar())
        tk.Button(topo, text="apagar tudo", command=self._apagar_tudo,
                  bg="#3a1412", fg="#ff5a4d", bd=0, font=("Segoe UI", 9, "bold"),
                  cursor="hand2", padx=10, pady=6).pack(side=tk.RIGHT)

        colunas = ("quando", "texto", "acao")
        self.tabela = ttk.Treeview(self, columns=colunas, show="headings", height=18)
        self.tabela.heading("quando", text="aprendida em")
        self.tabela.heading("texto", text="informação")
        self.tabela.column("quando", width=130, anchor="w")
        self.tabela.column("texto", width=430, anchor="w")
        self.tabela.column("acao", width=70, anchor="center")
        self.tabela.pack(fill=tk.BOTH, expand=True, padx=16, pady=(8, 16))
        self.tabela.tag_configure("apagavel", foreground="#c7d8e4")
        self.tabela.bind("<Button-1>", self._clique_apagar)

    def _listar(self):
        self.tabela.delete(*self.tabela.get_children())
        termo = self.var_busca.get().strip()
        itens = memory.buscar(termo) if termo else memory.todos()
        for it in itens:
            self.tabela.insert("", tk.END, values=(it["quando"], it["texto"], "✖ apagar"))

    def _clique_apagar(self, ev):
        regiao = self.tabela.identify("region", ev.x, ev.y)
        coluna = self.tabela.identify_column(ev.x)
        if regiao != "cell" or coluna != "#3":
            return
        linha = self.tabela.identify_row(ev.y)
        if not linha:
            return
        # índice real na memória = posição no filtro atual
        termo = self.var_busca.get().strip()
        itens = memory.buscar(termo) if termo else memory.todos()
        idx_na_tabela = self.tabela.index(linha)
        if 0 <= idx_na_tabela < len(itens):
            real = memory.todos().index(itens[idx_na_tabela])
            memory.apagar(real)
            if self.ao_apagar:
                self.ao_apagar()
            self._listar()

    def _apagar_tudo(self):
        memory.apagar_tudo()
        if self.ao_apagar:
            self.ao_apagar()
        self._listar()
