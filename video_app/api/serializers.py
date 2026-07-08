from rest_framework import serializers

from video_app.models import Video


class VideoListSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ["id", "created_at", "title", "description", "thumbnail_url", "category"]

    def get_thumbnail_url(self, obj):
        """Build the absolute URL to the video's thumbnail image."""
        request = self.context.get("request")
        if not obj.thumbnail:
            return None
        return request.build_absolute_uri(obj.thumbnail.url)