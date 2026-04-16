from django.urls import path

from .views import WeatherRiskView

urlpatterns = [
    path("weather/risk/", WeatherRiskView.as_view(), name="weather-risk"),
]
