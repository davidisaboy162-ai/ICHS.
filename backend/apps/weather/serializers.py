from rest_framework import serializers


class WeatherRiskRequestSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    location_name = serializers.CharField(required=False, allow_blank=True)
