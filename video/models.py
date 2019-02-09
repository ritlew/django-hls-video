from django.db import models


class VideoFile(models.Model):
    title = models.CharField(max_length=50)
    description = models.TextField()
    raw_video_file = models.FileField(upload_to="video/")
    processed = models.BooleanField(default=False)
    mpd_file = models.FilePathField(default=None, null=True)

