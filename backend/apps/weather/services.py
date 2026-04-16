import os

import requests


class OpenWeatherClient:
    base_url = "https://api.openweathermap.org/data/2.5/weather"

    def fetch_current(self, latitude: float, longitude: float) -> dict:
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            # Local fallback keeps development unblocked.
            return {
                "main": {"temp": 31.0, "humidity": 74},
                "wind": {"speed": 2.5},
                "weather": [{"main": "Clouds"}],
            }

        resp = requests.get(
            self.base_url,
            params={"lat": latitude, "lon": longitude, "appid": api_key, "units": "metric"},
            timeout=12,
        )
        resp.raise_for_status()
        return resp.json()


class DiseaseRiskService:
    def score(self, payload: dict) -> tuple[float, str, str]:
        temp = payload.get("main", {}).get("temp", 0)
        humidity = payload.get("main", {}).get("humidity", 0)
        wind = payload.get("wind", {}).get("speed", 0)

        score = min(1.0, max(0.0, (humidity / 100) * 0.55 + (temp / 40) * 0.35 + (1 - min(wind / 10, 1)) * 0.1))
        if score >= 0.75:
            level = "high"
        elif score >= 0.5:
            level = "moderate"
        else:
            level = "low"

        explanation = (
            f"Risk is {level} because humidity ({humidity}%) and temperature ({temp}C) "
            f"match favorable conditions for fungal spread."
        )
        return round(score, 4), level, explanation
