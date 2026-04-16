from rest_framework import generics, permissions

from .models import CommunityPost
from .serializers import CommunityPostSerializer


class CommunityPostListCreateView(generics.ListCreateAPIView):
    serializer_class = CommunityPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CommunityPost.objects.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
