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
    

class Video(models.Model):
    ### user facing elements
    title = models.CharField(max_length=50, default='Untitled')
    description = models.TextField(default='')
    collections = models.ManyToManyField(VideoCollection, related_name='videos')
    public = models.BooleanField(default=False)
    slug = AutoSlugField(populate_from='title', unique=True)

    ### interal logic elements
    # ID from chunked upload
    upload_id = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # json results from ffprobe as a string
    # use the vid_info property to access this as a dictionary
    vid_info_str = models.TextField(null=True)
    # path to the folder where the video files are stored
    # e.g. the variant videos and playlists, the thumbnail
    folder_path = models.CharField(max_length=100, null=True)
    # boolean expressing whether the video has finished processing or not
    processed = models.BooleanField(default=False)
    # celery task id of the processing tasks
    processing_id = models.CharField(max_length=100, null=True)
    # the master playlist for the HLS variants video stream
    master_playlist = models.FileField(null=True)
    thumbnail = models.FileField(null=True)

    @property
    def vid_info(self):
        return json.loads(self.vid_info_str)

    @property
    def play_time(self):
        duration = int(float(self.vid_info['format']['duration']))
        play_time_format = "%-H:%M:%S" if duration >= (60 * 60) else "%-M:%S"
        return time.strftime(play_time_format,  time.gmtime(duration))


class VideoVariant(models.Model):
    # Video that has the common information for this variant
    master = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='variants')
    # m3u8 playlist file for this variant
    playlist_file = models.FileField()
    # m4s video file for this variant
    video_file = models.FileField()
    # resolution that is an index of RESOLUTIONS defined at the top of this file
    resolution = models.SmallIntegerField()


class VideoChunkedUpload(ChunkedUpload):
    pass

