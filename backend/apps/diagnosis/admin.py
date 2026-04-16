from django.contrib import admin

from .models import DiagnosisReport, DiseaseClass


admin.site.register(DiseaseClass)
admin.site.register(DiagnosisReport)
