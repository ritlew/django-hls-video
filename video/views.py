from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import render
from django.conf import settings
from django.db import transaction
from django.core.paginator import Paginator

import json
import os

from chunked_upload.views import ChunkedUploadView, ChunkedUploadCompleteView
from sendfile import sendfile
from celery import group
from dal import autocomplete

from .forms import UploadModelForm
from .models import Video, VideoCollection, VideoUpload, MyChunkedUpload
from .tasks import setup_video_processing, create_thumbnail, create_variants


def video_index(request, collection=None):
    if collection:
        vid_results = Video.objects.filter(
            upload__collections__slug=collection,
            processed=True
        ).order_by("-pk")
        if not vid_results.count():
            raise Http404()
    else:
        vid_results = Video.objects.filter(processed=True).order_by("-pk")

    # pagination
    paginator = Paginator(vid_results, 6)

    page = request.GET.get('page', 1)
    vids = paginator.get_page(page)

    # https://stackoverflow.com/questions/30864011/display-only-some-of-the-page-numbers-by-django-pagination
    index = vids.number - 1
    num_extra = 2
    max_index = len(paginator.page_range)
    start_index = index - num_extra if index >= num_extra else 0
    end_index = index + (num_extra + 1) if index <= max_index - (num_extra + 1) else max_index
    page_range = list(paginator.page_range)[start_index:end_index]

    return render(request, "video/index.html", {
        "videos": vids,
        "page_range": page_range,
        "search": collection,
        "collections": VideoCollection.objects.all(),
    })

def process_video(request, vid_pk):
    vid_upload = VideoUpload.objects.get(pk=vid_pk)
    vid = Video(
        upload=vid_upload,
        processed=False,
        master_playlist=None,
        thumbnail=None
    )
    vid.save()

    processing_tasks = (
        setup_video_processing.s(vid.pk) |
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
            form.save_m2m()
            return JsonResponse({"message": "ok"})
    else:
        form = UploadModelForm()
    return render(request, 'video/form.html', {
        'form': form, 
        'websocket_protocol': settings.WEBSOCKET_PROTOCOL
    })


# https://django-autocomplete-light.readthedocs.io/en/master/tutorial.html
class CollectionAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return VideoCollection.objects.none()

        qs = VideoCollection.objects.all()

        if self.q:
            qs = qs.filter(title__istartswith=self.q)

        return qs


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

        vid = Video(
            upload=vid_upload,
            processed=False,
            master_playlist=None,
            thumbnail=None
        )
        vid.save()

        processing_tasks = (
            setup_video_processing.s(vid.pk) |
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
