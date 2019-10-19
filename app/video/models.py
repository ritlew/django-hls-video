from django.conf import settings
from django.db import models, transaction
from django.db.models import Max
from django.db.models.signals import post_init
from django.dispatch import receiver

from autoslug import AutoSlugField
from celery import group
from chunked_upload.models import ChunkedUpload
from ordered_model.models import OrderedModel

import json
import logging
import os
import time

RESOLUTIONS = [240, 360, 480, 720, 1080]

TRUE_FALSE_CHOICES = (
    (False, "No"),
    (True, "Yes"),
)

def format_seconds(seconds):
    play_time_format = "%-H:%M:%S" if seconds >= (60 * 60) else "%-M:%S"
    return time.strftime(play_time_format,  time.gmtime(seconds))


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
    public = models.BooleanField(default=False, choices=TRUE_FALSE_CHOICES)
    slug = AutoSlugField(populate_from='title', unique=True)
    thumbnail = models.FileField(null=True)
    gif_preview = models.FileField(null=True)
    collections = models.ManyToManyField(
        VideoCollection,
        related_name='videos',
        through='video.VideoCollectionOrder',
    )

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

    def __str__(self):
        return self.slug

    def begin_processing(self):
        if not self.processing_id:
            from .tasks import (
                setup_video_processing, create_thumbnail, create_variants, cleanup_video_processing
            )

            processing_tasks = (
                setup_video_processing.s(self.pk) |
                create_thumbnail.si(self.pk) |
                create_variants.si(self.pk) |
                cleanup_video_processing.si(self.pk)
            )

            res = processing_tasks.delay()
            with transaction.atomic():
                vid = Video.objects.select_for_update().get(pk=self.pk)
                vid.processing_id = res.parent.id
                vid.save()
        else:
            logging.error(f'{self.title}:{self.pk} attempted to process again while processing')

    @property
    def vid_info(self):
        return json.loads(self.vid_info_str)

    @property
    def duration(self):
        return int(float(self.vid_info['format']['duration']))

    @property
    def play_time(self):
        return format_seconds(self.duration)


class VideoPlaybackTracker(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    seconds = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.user} - {self.video}: {format_seconds(self.seconds)}'


class VideoVariant(models.Model):
    # Video that has the common information for this variant
    master = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='variants')
    # m3u8 playlist file for this variant
    playlist_file = models.FileField()
    # m4s video file for this variant
    video_file = models.FileField()
    # resolution that is an index of RESOLUTIONS defined at the top of this file
    resolution = models.SmallIntegerField()


class VideoCollectionOrder(OrderedModel):
    collection = models.ForeignKey(VideoCollection, null=False, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, null=False, on_delete=models.CASCADE)
    order_with_respect_to = 'collection'

    class Meta(OrderedModel.Meta):
        ordering = ('collection', 'order')
        pass

    def __str__(self):
        return f'{self.collection} #{self.order}: {self.video}'

    @property
    def display_order(self):
        return self.order + 1


# because the form save_2m2() does not call the .save() function,
# an extra signal handler must be defined here to populate the
# the 'order' field, as this is handled in the .save() function
# https://github.com/bfirsh/django-ordered-model/blob/master/ordered_model/models.py#L77
@receiver(post_init, sender=VideoCollectionOrder)
def default_order(sender, instance, **kwargs):
    if getattr(instance, instance.order_field_name) is None:
        c = instance.get_ordering_queryset().aggregate(Max(instance.order_field_name)).get(instance.order_field_name + '__max')
        setattr(instance, instance.order_field_name, 0 if c is None else c + 1)


class VideoChunkedUpload(ChunkedUpload):
    pass

