from django.db import models

from chunked_upload.models import ChunkedUpload

class VideoFile(models.Model):
    title = models.CharField(max_length=50)
    header = models.CharField(max_length=50, null=True)
    description = models.TextField()
    upload_id = models.CharField(max_length=50, null=True)
    raw_video_file = models.FileField(upload_to="video/", null=True)
    thumbnail = models.FilePathField(null=True)
    processed = models.BooleanField(default=False)
    mpd_file = models.FilePathField(default=None, null=True)
    thumbnail = models.FilePathField(default=None, null=True)

    @property
    def preview_text(self):
        return self.description[:450] + "..."


class MyChunkedUpload(ChunkedUpload):
    pass

MyChunkedUpload._meta.get_field('user').null = True

