"""Plugin: clima — dados meteorológicos em tempo real (Open-Meteo, sem chave)."""
import json
import urllib.request


def _chamar(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "JarvisUltra2026"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


TOOL = {
    "name": "clima",
    "description": ("Previsão do tempo em tempo real para uma cidade. "
                     "Sem chave, via Open-Meteo. Use quando perguntarem como está o tempo."),
    "parameters": {"type": "object",
                   "properties": {"cidade": {"type": "string",
                                             "description": "nome da cidade, ex: 'São Paulo'"}}},
    "required": ["cidade"],
}

_CODIGOS = {
    0: "céu limpo", 1: "predominantemente limpo", 2: "parcialmente nublado",
    3: "nublado", 45: "nevoeiro", 48: "nevoeiro com gelo", 51: "garoa fraca",
    53: "garoa", 55: "garoa forte", 61: "chuva fraca", 63: "chuva",
    65: "chuva forte", 71: "neve fraca", 73: "neve", 75: "neve forte",
    80: "pancadas leves", 81: "pancadas de chuva", 82: "pancadas violentas",
    95: "tempestade", 96: "tempestade com granizo", 99: "tempestade severa",
}


def run(cidade: str = "São Paulo") -> str:
    try:
        geo = _chamar("https://geocoding-api.open-meteo.com/v1/search?name="
                      + urllib.request.quote(cidade) + "&count=1&language=pt")
        if not geo.get("results"):
            return f"não achei a cidade '{cidade}'."
        local = geo["results"][0]
        dados = _chamar(
            f"https://api.open-meteo.com/v1/forecast?latitude={local['latitude']}"
            f"&longitude={local['longitude']}&current=temperature_2m,"
            "apparent_temperature,weather_code,wind_speed_10m")
        c = dados["current"]
        cond = _CODIGOS.get(int(c.get("weather_code", -1)), "—")
        return (f"{local.get('name', cidade)} agora: {c['temperature_2m']:.0f}°C "
                f"(sensação {c['apparent_temperature']:.0f}°C), {cond}, "
                f"vento {c['wind_speed_10m']:.0f} km/h.")
    except Exception as e:
        return f"clima indisponível (sem internet?): {str(e)[:90]}"
