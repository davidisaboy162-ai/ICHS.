from rest_framework import serializers

from .models import DiagnosisReport


class TextDiagnosisSerializer(serializers.Serializer):
    symptoms = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class ImageDiagnosisSerializer(serializers.Serializer):
    file = serializers.ImageField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class CombinedDiagnosisSerializer(serializers.Serializer):
    file = serializers.ImageField(required=False)
    symptoms = serializers.CharField(required=False, allow_blank=True)
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()

    def validate(self, attrs):
        if not attrs.get("file") and not attrs.get("symptoms"):
            raise serializers.ValidationError("Provide either an image, symptoms text, or both.")
        return attrs


class DiagnosisReportSerializer(serializers.ModelSerializer):
    disease_name = serializers.CharField(source="predicted_disease.name", read_only=True)

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
            "created_at",
        ]
