from rest_framework import serializers

from .models import DiagnosisReport


class TextDiagnosisSerializer(serializers.Serializer):
    symptoms = serializers.CharField()
    latitude = serializers.FloatField(required=False, default=0.0)
    longitude = serializers.FloatField(required=False, default=0.0)
    location_name = serializers.CharField(required=False, allow_blank=True, default="")


class ImageDiagnosisSerializer(serializers.Serializer):
    file = serializers.ImageField()
    latitude = serializers.FloatField(required=False, default=0.0)
    longitude = serializers.FloatField(required=False, default=0.0)
    location_name = serializers.CharField(required=False, allow_blank=True, default="")


class CombinedDiagnosisSerializer(serializers.Serializer):
    file = serializers.ImageField(required=False)
    symptoms = serializers.CharField(required=False, allow_blank=True)
    latitude = serializers.FloatField(required=False, default=0.0)
    longitude = serializers.FloatField(required=False, default=0.0)
    location_name = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if not attrs.get("file") and not attrs.get("symptoms"):
            raise serializers.ValidationError("Provide either an image, symptoms text, or both.")
        return attrs


class DiagnosisReportSerializer(serializers.ModelSerializer):
    disease_name = serializers.CharField(source="predicted_disease.name", read_only=True)
    alerts_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = DiagnosisReport
        fields = [
            "id",
            "input_type",
            "symptom_text",
            "confidence",
            "model_outputs",
            "latitude",
            "longitude",
            "disease_name",
            "alerts_count",
            "created_at",
        ]
