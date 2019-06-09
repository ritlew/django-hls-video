from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin

from .models import Video, VideoVariant, VideoCollection


class VideoInfoAdmin(SummernoteModelAdmin):
    summernote_fields = ('description',)
    readonly_fields = ['upload_id']


admin.site.register(VideoVariant)
admin.site.register(Video, VideoInfoAdmin)
admin.site.register(VideoCollection)
