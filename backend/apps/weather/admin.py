from django.contrib import admin

from .models import DiseaseRiskForecast, WeatherSnapshot


admin.site.register(WeatherSnapshot)
admin.site.register(DiseaseRiskForecast)
