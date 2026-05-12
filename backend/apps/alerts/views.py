from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.diagnosis.models import DiagnosisReport

from .models import OutbreakAlert
from .serializers import OutbreakAlertSerializer
from .services import AlertService


class AlertListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        latitude = request.query_params.get("latitude")
        longitude = request.query_params.get("longitude")
        radius = request.query_params.get("radius")

        if latitude is not None and longitude is not None:
            nearby = AlertService().get_nearby_reports(
                float(latitude),
                float(longitude),
                float(radius) if radius else None,
            )
            return Response({"mode": "nearby", "results": nearby})

        if request.user and request.user.is_authenticated:
            alerts = OutbreakAlert.objects.filter(recipient=request.user)
            return Response({"mode": "user", "results": OutbreakAlertSerializer(alerts, many=True).data})

        recent = DiagnosisReport.objects.select_related("predicted_disease").all()[:20]
        payload = [
            {
                "report_id": report.id,
                "disease": getattr(report.predicted_disease, "name", "Unknown"),
                "confidence": report.confidence,
                "latitude": report.latitude,
                "longitude": report.longitude,
                "created_at": report.created_at.isoformat(),
            }
            for report in recent
        ]
        return Response({"mode": "recent", "results": payload})
