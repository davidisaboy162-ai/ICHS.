from rest_framework import serializers

from .models import CommunityComment, CommunityPost


class CommunityCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.username", read_only=True)

    class Meta:
        model = CommunityComment
        fields = ["id", "author_name", "body", "created_at"]


class CommunityPostSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.username", read_only=True)
    comments = CommunityCommentSerializer(many=True, read_only=True)

    class Meta:
        model = CommunityPost
        fields = ["id", "author_name", "title", "body", "comments", "created_at"]
