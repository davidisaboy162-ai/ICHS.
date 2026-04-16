from django.contrib import admin

from .models import CommunityComment, CommunityPost


admin.site.register(CommunityPost)
admin.site.register(CommunityComment)
