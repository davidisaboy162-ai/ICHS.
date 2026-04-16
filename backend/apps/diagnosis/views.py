from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.alerts.services import AlertService

from .models import DiagnosisReport, DiseaseClass
from .serializers import (
    CombinedDiagnosisSerializer,
    DiagnosisReportSerializer,
    ImageDiagnosisSerializer,
    TextDiagnosisSerializer,
)
from .services import DiagnosisEngine

engine = DiagnosisEngine()


class PredictTextView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = TextDiagnosisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = engine.predict_from_text(serializer.validated_data["symptoms"])
        disease_obj, _ = DiseaseClass.objects.get_or_create(
            name=result.disease_name,
            defaults={"crop": "Unknown", "is_healthy_class": result.disease_name == "Healthy"},
        )

        report = DiagnosisReport.objects.create(
            created_by=request.user,
            input_type=DiagnosisReport.TEXT,
            symptom_text=serializer.validated_data["symptoms"],
            predicted_disease=disease_obj,
            confidence=result.confidence,
            model_outputs=result.raw_outputs,
            latitude=serializer.validated_data["latitude"],
            longitude=serializer.validated_data["longitude"],
        )
        AlertService().create_alerts_for_report(report)
        return Response(DiagnosisReportSerializer(report).data, status=status.HTTP_201_CREATED)


class PredictImageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ImageDiagnosisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = engine.predict_from_image(serializer.validated_data["file"])
        disease_obj, _ = DiseaseClass.objects.get_or_create(
            name=result.disease_name,
            defaults={"crop": "Unknown", "is_healthy_class": result.disease_name == "Healthy"},
        )

        report = DiagnosisReport.objects.create(
            created_by=request.user,
            input_type=DiagnosisReport.IMAGE,
            image=serializer.validated_data["file"],
            predicted_disease=disease_obj,
            confidence=result.confidence,
            model_outputs=result.raw_outputs,
            latitude=serializer.validated_data["latitude"],
            longitude=serializer.validated_data["longitude"],
        )
        AlertService().create_alerts_for_report(report)
        return Response(DiagnosisReportSerializer(report).data, status=status.HTTP_201_CREATED)


class PredictCombinedView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CombinedDiagnosisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = engine.predict_combined(
            serializer.validated_data.get("symptoms"),
            serializer.validated_data.get("file"),
        )
        disease_obj, _ = DiseaseClass.objects.get_or_create(
            name=result.disease_name,
            defaults={"crop": "Unknown", "is_healthy_class": result.disease_name == "Healthy"},
        )

        report = DiagnosisReport.objects.create(
            created_by=request.user,
            input_type=DiagnosisReport.COMBINED,
            symptom_text=serializer.validated_data.get("symptoms", ""),
            image=serializer.validated_data.get("file"),
            predicted_disease=disease_obj,
            confidence=result.confidence,
            model_outputs=result.raw_outputs,
            latitude=serializer.validated_data["latitude"],
            longitude=serializer.validated_data["longitude"],
        )
        AlertService().create_alerts_for_report(report)
        return Response(DiagnosisReportSerializer(report).data, status=status.HTTP_201_CREATED)
