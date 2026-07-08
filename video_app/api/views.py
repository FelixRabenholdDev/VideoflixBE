from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from video_app.models import Video

from .serializers import VideoListSerializer


class VideoListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        videos = Video.objects.all()
        serializer = VideoListSerializer(videos, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)