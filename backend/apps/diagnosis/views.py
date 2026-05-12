from __future__ import annotations

from django.db.models import Count
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.alerts.services import AlertService
from apps.weather.services import DiseaseRiskService, OpenWeatherClient

from .models import DiagnosisReport, DiseaseClass
from .serializers import (
    CombinedDiagnosisSerializer,
    DiagnosisReportSerializer,
    ImageDiagnosisSerializer,
    TextDiagnosisSerializer,
)
from .services import DiagnosisEngine

engine = DiagnosisEngine()


def _build_response(report: DiagnosisReport, extra=None):
    payload = DiagnosisReportSerializer(report).data
    payload["alerts_count"] = report.alerts.count()
    if extra:
        payload.update(extra)
    return payload


def _save_report(*, user, input_type, symptom_text, image, prediction, latitude, longitude):
    disease_obj, _ = DiseaseClass.objects.get_or_create(
        name=prediction.disease_name,
        defaults={"crop": "Unknown", "is_healthy_class": prediction.disease_name == "Healthy"},
    )
    report = DiagnosisReport.objects.create(
        created_by=user if getattr(user, "is_authenticated", False) else None,
        input_type=input_type,
        symptom_text=symptom_text or "",
        image=image,
        predicted_disease=disease_obj,
        confidence=prediction.confidence,
        model_outputs=prediction.raw_outputs,
        latitude=latitude,
        longitude=longitude,
    )
    AlertService().create_alerts_for_report(report)
    return report


class PredictTextView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = TextDiagnosisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = engine.predict_from_text(serializer.validated_data["symptoms"])
        report = _save_report(
            user=request.user,
            input_type=DiagnosisReport.TEXT,
            symptom_text=serializer.validated_data["symptoms"],
            image=None,
            prediction=result,
            latitude=serializer.validated_data["latitude"],
            longitude=serializer.validated_data["longitude"],
        )
        return Response(_build_response(report), status=status.HTTP_201_CREATED)


class PredictImageView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ImageDiagnosisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = engine.predict_from_image(serializer.validated_data["file"])
        report = _save_report(
            user=request.user,
            input_type=DiagnosisReport.IMAGE,
            symptom_text="",
            image=serializer.validated_data["file"],
            prediction=result,
            latitude=serializer.validated_data["latitude"],
            longitude=serializer.validated_data["longitude"],
        )
        return Response(_build_response(report), status=status.HTTP_201_CREATED)


class PredictCombinedView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CombinedDiagnosisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = engine.predict_combined(
            serializer.validated_data.get("symptoms"),
            serializer.validated_data.get("file"),
        )
        report = _save_report(
            user=request.user,
            input_type=DiagnosisReport.COMBINED,
            symptom_text=serializer.validated_data.get("symptoms", ""),
            image=serializer.validated_data.get("file"),
            prediction=result,
            latitude=serializer.validated_data["latitude"],
            longitude=serializer.validated_data["longitude"],
        )

        weather_payload = OpenWeatherClient().fetch_current(
            serializer.validated_data["latitude"],
            serializer.validated_data["longitude"],
        )

        risk_score, risk_level, explanation = DiseaseRiskService().score(weather_payload)
        response_payload = _build_response(
            report,
            extra={
                "weather_risk": {
                    "risk_score": risk_score,
                    "risk_level": risk_level,
                    "explanation": explanation,
                }
            },
        )
        return Response(response_payload, status=status.HTTP_201_CREATED)


class DiagnosisReportListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        queryset = DiagnosisReport.objects.select_related("predicted_disease").annotate(alerts_count=Count("alerts"))

        if request.query_params.get("latitude") and request.query_params.get("longitude"):
            try:
                latitude = float(request.query_params["latitude"])
                longitude = float(request.query_params["longitude"])
                radius = float(request.query_params.get("radius", 10))
                queryset = [
                    report
                    for report in queryset
                    if abs(report.latitude - latitude) <= radius / 111 and abs(report.longitude - longitude) <= radius / 111
                ]
            except ValueError:
                pass
        else:
            queryset = queryset[:20]

        data = DiagnosisReportSerializer(queryset, many=True).data
        return Response(data)
