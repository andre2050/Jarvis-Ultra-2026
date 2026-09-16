"""Plugins auto-descritivos — adicionar uma habilidade é arrastar 1 arquivo.

Um plugin é um .py em plugins/ com:
    TOOL = {"name": ..., "description": ..., "parameters": {...schema...}}
    def run(**kwargs) -> str
Nada mais. Descoberto automaticamente na inicialização.
"""
import importlib.util
import traceback
from pathlib import Path

PLUGINS_DIR = Path(__file__).resolve().parent.parent / "plugins"


class Registro:
    def __init__(self):
        self._tools: dict = {}
        self._erros: list = []
        self.carregar()

    def carregar(self) -> None:
        self._tools.clear()
        self._erros.clear()
        for arq in sorted(PLUGINS_DIR.glob("*.py")):
            if arq.name.startswith("_"):
                continue
            try:
                spec = importlib.util.spec_from_file_location(arq.stem, arq)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                tool = getattr(mod, "TOOL", None)
                run = getattr(mod, "run", None)
                if isinstance(tool, dict) and callable(run) and tool.get("name"):
                    self._tools[tool["name"]] = (tool, run)
            except Exception:
                self._erros.append(f"{arq.name}: {traceback.format_exc(limit=1)}")

    @property
    def erros(self) -> list:
        return list(self._erros)

    def nomes(self) -> list:
        return sorted(self._tools)

    def schemas(self) -> list:
        """Lista de TOOL dicts prontos pro function calling do Ollama."""
        return [dict(t[0]) for t in self._tools.values()]

    def executar(self, nome: str, args: dict) -> str:
        if nome not in self._tools:
            return f"plugin '{nome}' não existe"
        try:
            return str(self._tools[nome][1](**args) or "").strip() or "(sem retorno)"
        except Exception as e:
            return f"erro no plugin {nome}: {e}"
