from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin

from .models import VideoUpload, VideoVariant


class VideoUploadAdmin(SummernoteModelAdmin):
    summernote_fields = ('description',)
    readonly_fields = ['slug', 'processed', 'master_playlist', 'thumbnail', 'upload_id', 'task_id']


admin.site.register(VideoUpload, VideoUploadAdmin)
admin.site.register(VideoVariant)
