# Django imports
from django.contrib import messages
from django.conf import settings
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.http import (
    JsonResponse, Http404, HttpResponseBadRequest, HttpResponseServerError
)

# Python standard imports
import json
import os

# third-party imports
from celery import group
from chunked_upload.views import ChunkedUploadView, ChunkedUploadCompleteView
from dal import autocomplete
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from sendfile import sendfile

# local imports
from .forms import VideoUploadForm
from .models import Video, VideoCollection, VideoChunkedUpload
from .tasks import (
    setup_video_processing, create_thumbnail, create_variants, cleanup_video_processing
)

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
            video_results = video_results.filter(collections__slug=collection_request)
        if not self.request.user.is_authenticated:
            video_results = video_results.filter(public=True)

        return video_results

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        video_results = context['videos']
        collection_request = self.kwargs.get('collection', None)

        if self.request.user.is_authenticated:
            collections = VideoCollection.objects.all()
        else:
            # if user is not authenticated, only show public videos and connected collections
            collection_pks = video_results.values_list('collections', flat=True)
            collections = VideoCollection.objects.filter(id__in=collection_pks)

        context['collections'] = collections
        context['search'] = collection_request
        return context


class VideoPlayerView(DetailView):
    model = Video
    queryset = Video.objects.filter(processed=True)
    template_name = 'video/video_player.html'

    def get_object(self):
        slug = self.kwargs.get('slug')

        try:
            video = self.queryset.get(slug=slug)
        except Video.DoesNotExist:
            raise Http404()

        # if user doesn't have permission to request files for this video
        if not video.public and not self.request.user.is_authenticated:
            raise Http404()

        return video


class GetVideoFileView(VideoPlayerView):
    """
    Abstract view class to retreive a file for a specific video. Subclasses should
    implement the get_filename() function and this class contains all other code to
    reply to the request with that file.
    """
    queryset = Video.objects.filter()

    def get_filename(self):
        """
        This function needs to be implemented by subclasses.
        """
        raise HttpResponseServerError()

    def get(self, request, *args, **kwargs):
        path = os.path.join(settings.MEDIA_ROOT, self.get_filename())

        return sendfile(request, path)


class GetVideoThumbnailView(GetVideoFileView):
    def get_filename(self):
        return self.get_object().thumbnail.name


class GetMasterPlaylistView(GetVideoFileView):
    def get_filename(self):
        field = self.get_object().master_playlist

        if not field:
            raise Http404()

        return self.get_object().master_playlist.name


class GetVariantPlaylistView(GetVideoFileView):
    def get_filename(self):
        variant = self.kwargs.get('variant')
        field = self.get_object().variants.get(resolution=variant)

        if not field:
            raise Http404()

        return field.playlist_file.name


class GetVariantVideoView(GetVideoFileView):
    def get_filename(self):
        variant = self.kwargs.get('variant')
        field = self.get_object().variants.get(resolution=variant)

        if not field:
            raise Http404()

        return field.video_file.name


class SubmitVideoUpload(APIView):
    permission_classes = (IsAuthenticated,)
    template_name = 'video/upload_form.html'

    def get(self, request, format=None):
        return render(request, self.template_name, {
            'form': VideoUploadForm(),
            'websocket_protocol': settings.WEBSOCKET_PROTOCOL }
        )

    def post(self, request, format=None):
        form = VideoUploadForm(request.POST)
        if form.is_valid():
            upload_id = form.cleaned_data['upload_id']
            vid, created = Video.objects.get_or_create(upload_id=upload_id, user=request.user)

            # if the videos title was the default title
            if Video._meta.get_field('title').get_default() == vid.title:
                # nullify the slug so it can autopopulate again
                vid.slug = None

            vid.title = form.cleaned_data['title']
            vid.description = form.cleaned_data['description']
            vid.collections.set(form.cleaned_data['collections'])

            vid.save()
            return Response({}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': 'Form data is not valid'}, status=status.HTTP_400_BAD_REQUEST)


class DeleteVideoView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        upload_id = self.kwargs.get('upload_id', None)

        if not upload_id:
            messages.add_message(request, messages.ERROR, 'Something went wrong. Try again later.')

        try:
            video = Video.objects.get(upload_id=upload_id, user=request.user, processed=True)
            messages.add_message(request, messages.INFO, f'{video.title} deleted.')
            video.delete()
        except Video.DoesNotExist:
            messages.add_message(request, messages.ERROR, 'Something went wrong. Try again later.')

        return redirect('user_uploads')


class UserUploadsView(ListView):
    model = Video
    template_name = 'video/user_uploads.html'
    context_object_name = 'videos'
    paginate_by = 10

    def get_queryset(self):
        # if the user is requesting videos a specific collection
        if not self.request.user.is_authenticated:
            raise Http404()

        video_results = Video.objects.filter(user=self.request.user).order_by("-pk")

        return video_results


# https://django-autocomplete-light.readthedocs.io/en/master/tutorial.html
class CollectionAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return VideoCollection.objects.none()

        queryset = VideoCollection.objects.all().order_by('title')

        if self.q:
            queryset = queryset.filter(title__istartswith=self.q)

        return queryset


class VideoChunkedUploadView(ChunkedUploadView):
    model = VideoChunkedUpload
    field_name = 'raw_video_file'

    def check_permissions(self, request):
        return request.user.is_superuser or request.user.is_staff


class VideoChunkedUploadCompleteView(ChunkedUploadCompleteView):
    model = VideoChunkedUpload
    do_md5_check = False

    def check_permissions(self, request):
        return request.user.is_superuser or request.user.is_staff

    def on_completion(self, uploaded_file, request):
        vid, created = Video.objects.get_or_create(user=request.user, upload_id=request.POST.get("upload_id"))

        processing_tasks = (
            setup_video_processing.s(vid.pk) |
            group(
                create_thumbnail.si(vid.pk),
                create_variants.si(vid.pk)
            ) |
            cleanup_video_processing.si(vid.pk)
        )

        res = processing_tasks.delay()
        with transaction.atomic():
            vid = Video.objects.select_for_update().get(pk=vid.pk)
            res.parent.save()
            vid.processing_id = res.parent.id
            vid.save()

        return JsonResponse({"message": "file upload success"})


    def get_response_data(self, chunked_upload, request):
        return {'message': ("You successfully uploaded '%s' (%s bytes)!" %
(chunked_upload.filename, chunked_upload.offset))}

