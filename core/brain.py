"""Cérebro do Jarvis Ultra 2026 — Ollama offline + plugins auto-descritivos.

Janela deslizante de contexto (sessões ilimitadas por compressão de janela):
o prompt exibe o que cabe, o resto vive na memória recuperável.
"""
import platform
import sys
import threading

from core import ollama, plugins

MAX_RODADAS_TOOL = 6      # até 6 rodadas de function calling por resposta
JANELA = 30               # janela deslizante de mensagens


class Cerebro:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.registro = plugins.Registro()
        self.historico: list = []
        self._lock = threading.Lock()

    # ---------- autoconhecimento em tempo de execução ----------

    def _prompt_sistema(self) -> str:
        nome = self.cfg.get("nome_assistente", "Jarvis")
        usuario = self.cfg.get("usuario", "André")
        ferramentas = ", ".join(self.registro.nomes()) or "nenhuma"
        return (
            f"Você é {nome}, um assistente de IA pessoal no estilo J.A.R.V.I.S do Homem de Ferro. "
            f"Chame o usuário de '{usuario}' (ou 'senhor' com naturalidade). "
            "Personalidade: mordomo britânico — educado, direto, levemente espirituoso, nunca robótico. "
            f"Responda SEMPRE em português do Brasil, frases curtas e faladas (o texto vira voz). "
            f"Você roda localmente via Ollama no {sys.platform} / {platform.system()}. "
            f"Seu dono é {usuario}. Plugins disponíveis agora: {ferramentas}. "
            "Use plugins quando fizerem sentido; se uma tarefa for impossível, diga com franqueza. "
            "Memórias do usuário estão disponíveis via plugins de memória — use-os."
        )

    # ---------- loop de conversa ----------

    def responder(self, texto: str, ao_pensar=None) -> str:
        """Responde usando até MAX_RODADAS_TOOL de function calling."""
        host = self.cfg.get("ollama_host")
        modelo = self.cfg.get("ollama_model", "llama3.2")
        with self._lock:
            self.historico.append({"role": "user", "content": texto})
            msgs = ([{"role": "system", "content": self._prompt_sistema()}]
                    + self.historico[-JANELA:])
            try:
                for rodada in range(MAX_RODADAS_TOOL):
                    if ao_pensar:
                        ao_pensar(rodada)
                    r = ollama.chat(host, modelo, msgs, tools=self.registro.schemas() or None)
                    if not r["tool_calls"]:
                        resposta = r["texto"] or "…"
                        self.historico.append({"role": "assistant", "content": resposta})
                        return resposta
                    for chamada in r["tool_calls"]:
                        resultado = self.registro.executar(chamada["name"], chamada["args"])
                        msgs.append({"role": "assistant", "content": r["texto"] or "",
                                     "tool_calls": [{"function": {"name": chamada["name"],
                                                                  "arguments": chamada["args"]}}]})
                        msgs.append({"role": "tool", "content": str(resultado)[:4000],
                                     "tool_name": chamada["name"]})
                return "senhor, não consegui concluir essa tarefa com os plugins disponíveis."
            except Exception as e:
                if "Connection" in str(e) or "refused" in str(e).lower():
                    return ("estou offline, senhor — o servidor Ollama não responde. "
                            "Inicie o Ollama no PC e tente de novo.")
                return f"erro no cérebro: {str(e)[:200]}"
