from django.conf import settings
from django.db import models


class OutbreakAlert(models.Model):
    report = models.ForeignKey(
        "diagnosis.DiagnosisReport",
        on_delete=models.CASCADE,
        related_name="alerts",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_alerts",
    )
    distance_km = models.FloatField()
    delivered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("report", "recipient")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Alert to {self.recipient} ({self.distance_km:.2f}km)"
