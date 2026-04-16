from django.conf import settings
from django.db import models


class DiseaseClass(models.Model):
    name = models.CharField(max_length=120, unique=True)
    crop = models.CharField(max_length=120)
    is_healthy_class = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.crop} - {self.name}"


class DiagnosisReport(models.Model):
    IMAGE = "image"
    TEXT = "text"
    COMBINED = "combined"
    INPUT_CHOICES = [
        (IMAGE, "Image"),
        (TEXT, "Text"),
        (COMBINED, "Combined"),
    ]

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="diagnosis_reports",
    )
    input_type = models.CharField(max_length=20, choices=INPUT_CHOICES)
    symptom_text = models.TextField(blank=True)
    image = models.ImageField(upload_to="diagnosis_images/", null=True, blank=True)
    predicted_disease = models.ForeignKey(
        DiseaseClass,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    confidence = models.FloatField(default=0.0)
    model_outputs = models.JSONField(default=dict, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.input_type} diagnosis @ {self.created_at.isoformat()}"
