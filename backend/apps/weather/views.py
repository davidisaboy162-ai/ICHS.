from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DiseaseRiskForecast, WeatherSnapshot
from .serializers import WeatherRiskRequestSerializer
from .services import DiseaseRiskService, OpenWeatherClient


class WeatherRiskView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = WeatherRiskRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lat = serializer.validated_data["latitude"]
        lon = serializer.validated_data["longitude"]

        payload = OpenWeatherClient().fetch_current(lat, lon)
        snapshot = WeatherSnapshot.objects.create(
            latitude=lat,
            longitude=lon,
            temperature_c=payload.get("main", {}).get("temp", 0),
            humidity=payload.get("main", {}).get("humidity", 0),
            wind_speed=payload.get("wind", {}).get("speed", 0),
            condition=(payload.get("weather", [{}])[0]).get("main", ""),
            source_payload=payload,
        )

        score, level, explanation = DiseaseRiskService().score(payload)
        forecast = DiseaseRiskForecast.objects.create(
            location_name=serializer.validated_data.get("location_name", ""),
            latitude=lat,
            longitude=lon,
            risk_score=score,
            risk_level=level,
            explanation=explanation,
            snapshot=snapshot,
        )

        return Response(
            {
                "risk_score": forecast.risk_score,
                "risk_level": forecast.risk_level,
                "explanation": forecast.explanation,
                "weather": {
                    "temperature_c": snapshot.temperature_c,
                    "humidity": snapshot.humidity,
                    "condition": snapshot.condition,
                },
            },
            status=status.HTTP_201_CREATED,
        )
