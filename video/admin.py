from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin

from .models import VideoUpload, Video, VideoVariant, VideoCollection


class VideoUploadAdmin(SummernoteModelAdmin):
    summernote_fields = ('description',)
    readonly_fields = ['upload_id']


admin.site.register(VideoUpload, VideoUploadAdmin)
admin.site.register(VideoVariant)
admin.site.register(Video)
admin.site.register(VideoCollection)
