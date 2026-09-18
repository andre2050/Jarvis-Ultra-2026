"""Plugin: mensagens — prepara WhatsApp/Telegram com o texto pronto pra enviar."""
import webbrowser
from urllib.parse import quote

TOOL = {
    "name": "enviar_mensagem",
    "description": ("Abre o WhatsApp (ou Telegram) já com a mensagem digitada, pronta "
                    "pra você só apertar enviar. Recebe destinatário, texto e plataforma."),
    "parameters": {"type": "object",
                   "properties": {
                       "destinatario": {"type": "string",
                                        "description": "telefone com DDI (ex.: 5511999998888) ou @usuário do Telegram"},
                       "texto": {"type": "string", "description": "a mensagem a enviar"},
                       "plataforma": {"type": "string",
                                      "description": "whatsapp (padrão) ou telegram"}},
                   },
    "required": ["destinatario", "texto"],
}


def run(destinatario: str, texto: str, plataforma: str = "whatsapp") -> str:
    dest = destinatario.strip().lstrip("+").replace(" ", "").replace("-", "")
    corpo = texto.strip()
    if not corpo:
        return "sem texto pra enviar, senhor — me diga a mensagem."
    plat = (plataforma or "whatsapp").strip().lower()
    if plat in ("telegram", "tg"):
        usuario = dest.lstrip("@")
        if not usuario.isdigit() and not usuario.startswith("@"):
            usuario = "@" + usuario
        webbrowser.open(f"https://t.me/{usuario.lstrip('@')}?text={quote(corpo)}")
        return f"Telegram aberto com a mensagem pronta pra {destinatario.strip()}: aperte enviar."
    if not dest.isdigit():
        return ("pro WhatsApp preciso do número com DDI, só dígitos "
                "(ex.: 5511999998888).")
    webbrowser.open(f"https://wa.me/{dest}?text={quote(corpo)}")
    preview = corpo[:50] + ("…" if len(corpo) > 50 else "")
    return (f"WhatsApp aberto com a mensagem pronta pra +{dest}: "
            f"“{preview}” — só confirmar o envio, senhor.")
