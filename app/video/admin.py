from django.contrib import admin

from .models import (
    Video, VideoVariant, VideoCollection, VideoTag,
    VideoChunkedUpload, VideoCollectionOrder,
    VideoPlaybackTracker
)

class VideoInfoAdmin(admin.ModelAdmin):
    readonly_fields = ['upload_id']


admin.site.register(VideoVariant)
admin.site.register(Video, VideoInfoAdmin)
admin.site.register(VideoCollection)
admin.site.register(VideoTag)
admin.site.register(VideoChunkedUpload)
admin.site.register(VideoCollectionOrder)
admin.site.register(VideoPlaybackTracker)
