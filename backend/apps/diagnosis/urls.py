from django.urls import path

from .views import DiagnosisReportListView, PredictCombinedView, PredictImageView, PredictTextView

urlpatterns = [
    path("predict/text/", PredictTextView.as_view(), name="predict-text"),
    path("predict/image/", PredictImageView.as_view(), name="predict-image"),
    path("predict/combined/", PredictCombinedView.as_view(), name="predict-combined"),
    path("diagnosis/reports/", DiagnosisReportListView.as_view(), name="diagnosis-reports"),
    path("diagnosis/combined/", PredictCombinedView.as_view(), name="diagnosis-combined"),
]
