from rest_framework import serializers

from .models import OutbreakAlert


class OutbreakAlertSerializer(serializers.ModelSerializer):
    disease_name = serializers.CharField(source="report.predicted_disease.name", read_only=True)

    class Meta:
        model = OutbreakAlert
        fields = ["id", "disease_name", "distance_km", "delivered", "created_at"]
