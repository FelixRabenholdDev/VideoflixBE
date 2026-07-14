from django.db.models.signals import post_save
from django.dispatch import receiver
from django_rq import enqueue

from .jobs import convert_video_to_hls, generate_thumbnail
from .models import Video


@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    """Queue the HLS conversion job whenever a new video is uploaded."""
    if created:
        enqueue(generate_thumbnail, instance.id)
        enqueue(convert_video_to_hls, instance.id)