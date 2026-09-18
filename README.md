# J.A.R.V.I.S — Ultra 2026 🛰

Assistente de IA pessoal estilo Homem de Ferro. **100% offline por natureza** (cérebro Ollama),
com voz à prova de falhas, plugins auto-descritivos e HUD holográfico reativo.

> Reconstruído do zero em setembro de 2026 — sem herança de bugs do projeto anterior.

## Estado atual (v0.2.0 — VOZ E PRESENÇA)

**Tudo da fundação, mais o rosto:**

- 🧑‍🎤 **Avatar holográfico** — cabeça humana animada por software: dublagem real
  (~50 formas de boca/s a partir dos visemas do texto), sobrancelhas, olhar,
  piscadas, acenos. Rosto como status: pensa, ouve, fala, dorme
- 🎙 **Wake word local** — "Ei, Jarvis" detectado no próprio PC (openwakeword;
  sem openwakeword, o Vosk ouve tudo e filtra na mão)
- ⌨️ **Push-to-talk global** — Ctrl+Espaço em qualquer app
- 🔇 **Anti-eco** — nunca responde à própria voz
- 🧠 **Painel de memória** — veja e apague o que ele sabe, por item
- 🧩 **+4 plugins**: clima, busca web, telemetria de hardware, processador de arquivos

### Fundação (v0.1.0)

- 🧠 **Cérebro Ollama offline** com function calling (llama3.1+, qwen2.5, mistral-nemo…)
- 🧩 **Plugins auto-descritivos** — arraste um `.py` em `plugins/`, vira habilidade na próxima inicialização
- 🎙 **Voz em cadeia** — pyttsx3 → TTS nativo do Windows (PowerShell System.Speech). Nunca fica mudo
- 🎨 **HUD reativo recolorível ao vivo** — qualquer hex recolori a interface
- 🧠 **Memória persistente ilimitada** — salva, busca, lista, apaga; nada esquecido em silêncio
- ♾️ **Janela deslizante** de contexto — sessões longas sem estourar o prompt
- 🪪 **Autoconhecimento em runtime** — nome, SO, capacidades e plugins no prompt de sistema
- ⚠️ **Diagnóstico honesto** — offline, sem voz ou plugin quebrado: você fica sabendo, com o motivo

## Rodar

```bash
pip install -r requirements.txt   # requests · psutil · pyttsx3
# presença v0.2.0 (recomendado): pip install sounddevice vosk keyboard openwakeword
# instale o Ollama em https://ollama.com e: ollama pull llama3.2
python main.py
```

## Estrutura

```
core/       config · ollama · brain · plugins · memory · voice
ui/         hud (holograma reativo)
plugins/    hora · telemetria · navegador · memoria   ← adicione skills aqui
```

Um plugin é o arquivo mais simples possível:

```python
TOOL = {"name": "minha_skill", "description": "o que faz",
        "parameters": {"type": "object", "properties": {}}}
def run() -> str:
    return "pronto!"
```

## Roadmap → visão completa

Ver [docs/ROADMAP.md](docs/ROADMAP.md) — de desktop único até plataforma completa
(desktop + web + celular), avatar holográfico com dublagem, wake word, agente de tarefas e mais.
