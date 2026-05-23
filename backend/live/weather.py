"""Open-Meteo Forecast API — current weather in Phuket. No API key required."""
import requests
from datetime import datetime

PHUKET_LAT = 7.88
PHUKET_LON = 98.39
URL = "https://api.open-meteo.com/v1/forecast"


def get_current_weather() -> dict:
    try:
        res = requests.get(URL, params={
            "latitude": PHUKET_LAT,
            "longitude": PHUKET_LON,
            "current": "temperature_2m,rain,wind_speed_10m,weather_code",
            "timezone": "Asia/Bangkok",
        }, timeout=5)
        res.raise_for_status()
        c = res.json()["current"]

        rain = float(c.get("rain", 0))
        temp = float(c["temperature_2m"])
        wind = float(c["wind_speed_10m"])
        code = int(c.get("weather_code", 0))

        if rain > 10:
            condition = "heavy rain — significant traffic slowdown expected"
        elif rain > 2:
            condition = "light rain — moderate impact on traffic"
        elif code in range(51, 70) or code in range(80, 100):
            condition = "rain showers — some traffic impact"
        else:
            condition = "dry — good driving conditions"

        return {
            "temperature_c": round(temp, 1),
            "rain_mm": round(rain, 1),
            "wind_kmh": round(wind, 1),
            "condition": condition,
            "timestamp": c.get("time", datetime.now().isoformat()),
            "source": "Open-Meteo Forecast API",
        }
    except Exception as e:
        return {"error": str(e), "source": "Open-Meteo"}


def format_for_prompt(w: dict) -> str:
    if "error" in w:
        return f"[Live weather unavailable: {w['error']}]"
    return (
        f"LIVE WEATHER (right now, Phuket):\n"
        f"  Temperature: {w['temperature_c']}°C | "
        f"Rain: {w['rain_mm']}mm | Wind: {w['wind_kmh']} km/h\n"
        f"  Condition: {w['condition']}"
    )
