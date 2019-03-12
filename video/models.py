from django.conf import settings
from django.db import models

from chunked_upload.models import ChunkedUpload
from autoslug import AutoSlugField
from celery import group

import json
import os
import time

RESOLUTIONS = [240, 360, 480, 720, 1080]


class VideoCollection(models.Model):
    title = models.CharField(max_length=50)
    description = models.CharField(max_length=50, null=True)
    slug = AutoSlugField(populate_from='title', unique=True)

    def __str__(self):
        return self.title
    

class VideoUpload(models.Model):
    # form elements
    title = models.CharField(max_length=50)
    description = models.TextField()
    collections = models.ManyToManyField(VideoCollection, related_name='videos')
    raw_video_file = models.FileField(
        null=True, # required for chunked upload
        upload_to=os.path.join(settings.SENDFILE_REL_PATH, 'video/')
    )
    upload_id = models.CharField(max_length=50, null=True)

class Video(models.Model):
    upload = models.OneToOneField(VideoUpload, on_delete=models.CASCADE)
    vid_info_str = models.TextField(null=True)
    folder_path = models.CharField(max_length=100, null=True)
    slug = AutoSlugField(populate_from='title', unique=True)
    processed = models.BooleanField(default=False)
    processing_id = models.CharField(max_length=100, null=True)
    master_playlist = models.FileField(null=True)
    thumbnail = models.FileField(null=True)

    @property
    def title(self):
        return self.upload.title

    @property
    def vid_info(self):
        return json.loads(self.vid_info_str)

    @property
    def play_time(self):
        duration = int(float(self.vid_info['format']['duration']))
        play_time_format = "%-H:%M:%S" if duration >= (60 * 60) else "%-M:%S"
        return time.strftime(play_time_format,  time.gmtime(duration))


class VideoVariant(models.Model):
    master = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='variants')
    playlist_file = models.FileField()
    video_file = models.FileField()
    resolution = models.SmallIntegerField()


class MyChunkedUpload(ChunkedUpload):
    pass
MyChunkedUpload._meta.get_field('user').null = True

