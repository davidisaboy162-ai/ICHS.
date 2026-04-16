from django.urls import path

from .views import CommunityPostListCreateView

urlpatterns = [
    path("community/posts/", CommunityPostListCreateView.as_view(), name="community-posts"),
]
