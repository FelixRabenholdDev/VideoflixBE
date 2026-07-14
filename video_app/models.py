from django.db import models

class Video(models.Model):
    class Category(models.TextChoices):
        DRAMA = "Drama", "Drama"
        ROMANCE = "Romance", "Romance"
        COMEDY = "Comedy", "Comedy"
        ACTION = "Action", "Action"
        DOCUMENTARY = "Documentary", "Documentary"

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to="thumbnails/", blank=True, null=True)
    video_file = models.FileField(upload_to="uploads/")
    category = models.CharField(max_length=100, choices=Category.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title