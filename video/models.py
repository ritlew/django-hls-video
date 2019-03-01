from django.conf import settings
from django.db import models

from chunked_upload.models import ChunkedUpload
from autoslug import AutoSlugField

import os

RESOLUTIONS = [240, 360, 480, 720, 1080]

class VideoUpload(models.Model):
    # form elements
    title = models.CharField(max_length=50)
    description = models.TextField()
    collection = models.CharField(max_length=100)
    raw_video_file = models.FileField(
        null=True, # required for chunked upload
        upload_to=os.path.join(settings.SENDFILE_REL_PATH, 'video/')
    )

    # non-form elements
    slug = AutoSlugField(populate_from='title', unique=True)
    processed = models.BooleanField(default=False)
    master_playlist = models.FileField(null=True)
    thumbnail = models.FileField(null=True)
    upload_id = models.CharField(max_length=50, null=True)
    task_id = models.CharField(max_length=50)

    @property
    def preview_text(self):
        return self.description[:450] + '...'


class VideoVariant(models.Model):
    master = models.ForeignKey(VideoUpload, on_delete=models.CASCADE, related_name='variants')
    playlist_file = models.FileField()
    video_file = models.FileField()
    resolution = models.SmallIntegerField()


class MyChunkedUpload(ChunkedUpload):
    pass
MyChunkedUpload._meta.get_field('user').null = True

