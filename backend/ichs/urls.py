from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "healthy", "service": "ICHS Django API"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", HealthCheckView.as_view(), name="health-check"),
    path("api/v1/auth/", include("apps.users.urls")),
    path("api/v1/", include("apps.diagnosis.urls")),
    path("api/v1/", include("apps.alerts.urls")),
    path("api/v1/", include("apps.weather.urls")),
    path("api/v1/", include("apps.community.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
