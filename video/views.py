from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.conf import settings
from django.db import transaction

import json
import os

from chunked_upload.views import ChunkedUploadView, ChunkedUploadCompleteView
from sendfile import sendfile
from celery import group

from .forms import UploadModelForm
from .models import VideoUpload, Video, MyChunkedUpload
from .tasks import setup_video_processing, create_thumbnail, create_variants


def video_index(request):
    vids = Video.objects.filter(processed=True).order_by("-pk")[:10]
    return render(request, "video/index.html", {"videos": vids})

def process_video(request, vid_pk):
    vid = VideoUpload.objects.get(pk=vid_pk)
    process_video_file.delay(vid.pk)
    return HttpResponse("ok")


def get_video(request, video_slug, filetype):
    if request.user.is_authenticated:
        v = Video.objects.get(slug=video_slug)
        switcher = {
            "thumbnail": v.thumbnail.name,
            "video": v.master_playlist.name,
        }
        filename = switcher.get(filetype, None)
        if not filename:
            if "m4s" in filetype:
                filename = v.variants.get(resolution=os.path.splitext(filetype)[0]).video_file.name
            else:
                filename = v.variants.get(resolution=os.path.splitext(filetype)[0]).playlist_file.name
        path = os.path.join(settings.MEDIA_ROOT, filename)
        r = sendfile(request, path)
        return r
    return HttpResponse("not so ok...")


def video_player(request, video_slug):
    vid_object = Video.objects.get(slug=video_slug)
    
    if not vid_object.processed:
        return render(request, "video/video_player.html")

    return render(request, "video/video_player.html", {"vid": vid_object})

def form_view(request):
    if request.method == 'POST':
        # stop attempted file upload on this endpoint
        form = UploadModelForm(request.POST)
        if form.is_valid():
            vid = form.save(commit=False)
            vid.upload_id = request.POST.get("upload_id")
            vid.save()
            return JsonResponse({"message": "ok"})
    else:
        form = UploadModelForm()
    return render(request, 'video/form.html', {'form': form})

class MyChunkedUploadView(ChunkedUploadView):

    model = MyChunkedUpload
    field_name = 'raw_video_file'

    def check_permissions(self, request):
        # Allow non authenticated users to make uploads
        pass


class MyChunkedUploadCompleteView(ChunkedUploadCompleteView):

    model = MyChunkedUpload
    do_md5_check = False

    def check_permissions(self, request):
        # Allow non authenticated users to make uploads
        pass

    def on_completion(self, uploaded_file, request):
        vid_upload = VideoUpload.objects.get(upload_id=request.POST.get("upload_id"))
        vid_upload.raw_video_file = uploaded_file
        vid_upload.save()

        vid = Video(
            upload=vid_upload,
            processed=False,
            master_playlist=None,
            thumbnail=None
        )
        vid.save()

        processing_tasks = (
            setup_video_processing.s(vid_upload.pk, vid.pk) |
            group(
                create_thumbnail.si(vid.pk),
                create_variants.si(vid.pk)
            )
        )

        res = processing_tasks.delay()
        with transaction.atomic():
            vid = Video.objects.get(pk=vid.pk)
            res.save()
            vid.processing_id = res.id
            vid.save()

        return JsonResponse({"message": "file upload success"})
        

    def get_response_data(self, chunked_upload, request):
        return {'message': ("You successfully uploaded '%s' (%s bytes)!" %
(chunked_upload.filename, chunked_upload.offset))}
