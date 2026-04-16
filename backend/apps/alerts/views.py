from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import OutbreakAlert
from .serializers import OutbreakAlertSerializer


class AlertListView(generics.ListAPIView):
    serializer_class = OutbreakAlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return OutbreakAlert.objects.filter(recipient=self.request.user)
