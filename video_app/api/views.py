from django.http import FileResponse, Http404

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from video_app.models import Video
from video_app.utils import build_manifest_path, is_valid_resolution

from .serializers import VideoListSerializer


class VideoListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        videos = Video.objects.all()
        serializer = VideoListSerializer(videos, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class VideoManifestView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution):
        self._ensure_video_exists(movie_id)
        manifest_path = self._resolve_manifest_path(movie_id, resolution)
        return FileResponse(open(manifest_path, "rb"), content_type="application/vnd.apple.mpegurl")

    def _ensure_video_exists(self, movie_id):
        """Raise 404 if no video with the given id exists."""
        if not Video.objects.filter(pk=movie_id).exists():
            raise Http404("Video not found.")

    def _resolve_manifest_path(self, movie_id, resolution):
        """Raise 404 if the resolution is invalid or the manifest file is missing."""
        if not is_valid_resolution(resolution):
            raise Http404("Manifest not found.")
        path = build_manifest_path(movie_id, resolution)
        if not path.exists():
            raise Http404("Manifest not found.")
        return path