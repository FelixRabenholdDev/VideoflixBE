from django.db.models.signals import post_save
from django.dispatch import receiver
from django_rq import enqueue

from .jobs import convert_video_to_hls, generate_thumbnail
from .models import Video


@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    """Queue HLS conversion whenever a video is created. Auto-generate a
    thumbnail only if none has been provided (manually or previously)."""
    if created:        
        enqueue(convert_video_to_hls, instance.id)
    elif not instance.thumbnail:
        enqueue(generate_thumbnail, instance.id)