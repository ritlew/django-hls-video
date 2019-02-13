from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin

from .models import VideoFile


class VideoFileAdmin(SummernoteModelAdmin):
    summernote_fields = ('description',)
    readonly_fields = ['mpd_file', 'processed']


admin.site.register(VideoFile, VideoFileAdmin)
