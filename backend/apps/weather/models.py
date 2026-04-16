from django.db import models


class WeatherSnapshot(models.Model):
    latitude = models.FloatField()
    longitude = models.FloatField()
    temperature_c = models.FloatField()
    humidity = models.FloatField()
    wind_speed = models.FloatField(default=0)
    condition = models.CharField(max_length=80, blank=True)
    source_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class DiseaseRiskForecast(models.Model):
    location_name = models.CharField(max_length=120, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    risk_score = models.FloatField()
    risk_level = models.CharField(max_length=20)
    explanation = models.TextField(blank=True)
    snapshot = models.ForeignKey(WeatherSnapshot, on_delete=models.CASCADE, related_name="forecasts")
    created_at = models.DateTimeField(auto_now_add=True)
