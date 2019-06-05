# Django imports
from django.conf import settings
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import render
from django.views.generic.list import ListView

# Python standard imports
import json
import os

# third-party imports
from celery import group
from chunked_upload.views import ChunkedUploadView, ChunkedUploadCompleteView
from dal import autocomplete
from sendfile import sendfile

# local imports
from .forms import UploadModelForm
from .models import Video, VideoCollection, VideoUpload, MyChunkedUpload
from .tasks import setup_video_processing, create_thumbnail, create_variants

class VideoListView(ListView):
    model = Video
    template_name = 'video/index.html'
    context_object_name = 'videos'
    paginate_by = 10

    def get_queryset(self):
        collection_request = self.kwargs.get('collection', None)

        video_results = Video.objects.filter(processed=True).order_by("-pk")

        # if the user is requesting videos a specific collection
        if collection_request:
            video_results = video_results.filter(upload__collections__slug=collection_request)

        return video_results

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        video_results = context['videos']
        collection_request = self.kwargs.get('collection', None)

        if self.request.user.is_authenticated:
            collections = VideoCollection.objects.all()
        else:
            # if user is not authenticated, only show public videos and connected collections
            video_results = video_results.filter(upload__public=True)
            collection_pks = video_results.values_list('upload__collections', flat=True)
            collections = VideoCollection.objects.filter(id__in=collection_pks)

        context['collections'] = collections
        context['search'] = collection_request
        return context

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


def video_player(request, video_slug):
    vid_object = Video.objects.get(slug=video_slug)
    
    if not vid_object.processed:
        return render(request, "video/video_player.html")

    return render(request, "video/video_player.html", {"vid": vid_object})

def form_view(request):
    if not request.user.is_authenticated:
        return Http404()

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
            user=request.user,
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
