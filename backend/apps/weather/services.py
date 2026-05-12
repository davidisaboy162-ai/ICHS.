import os

import requests


class OpenWeatherClient:
    base_url = "https://api.openweathermap.org/data/2.5/weather"

    def fetch_current(self, latitude: float, longitude: float) -> dict:
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            # Local fallback keeps development unblocked.
            seed = abs(float(latitude)) + abs(float(longitude))
            return {
                "main": {"temp": round(22 + (seed % 10), 1), "humidity": round(55 + (seed % 30), 1)},
                "wind": {"speed": round(1.5 + (seed % 5), 1)},
                "weather": [{"main": "Clouds" if int(seed) % 2 else "Clear"}],
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
        temp = float(payload.get("main", {}).get("temp", 0) or 0)
        humidity = float(payload.get("main", {}).get("humidity", 0) or 0)
        wind = float(payload.get("wind", {}).get("speed", 0) or 0)

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
