# Django imports
from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction, DatabaseError
from django.db.models import Q
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.views.generic.base import View, TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.utils.decorators import method_decorator
from django.http import (
    HttpResponse, JsonResponse, Http404, HttpResponseBadRequest, HttpResponseServerError
)

# Python standard imports
import json
import logging
import os
import shlex
import sys
import subprocess

# third-party imports
from celery import group
from chunked_upload.views import ChunkedUploadView, ChunkedUploadCompleteView
from dal import autocomplete
from sendfile import sendfile

# local imports
from .forms import VideoUploadForm
from .models import (
    Video, VideoCollection, VideoChunkedUpload, VideoCollectionOrder,
    VideoPlaybackTracker, RESOLUTIONS
)
from .decorators import auth_or_404

class VideoListView(ListView):
    model = Video
    template_name = 'video/index.html'
    context_object_name = 'videos'
    paginate_by = 10

    def get_queryset(self):
        collection_request = self.kwargs.get('collection', None)

        # if the user is requesting videos a specific collection
        if collection_request:
            order_results = VideoCollectionOrder.objects.filter(
                collection__slug=collection_request,
                video__processed=True
            ).values_list('video', flat=True).order_by("order")
            video_results = Video.objects.filter(pk__in=order_results)
        else:
            video_results = Video.objects.filter(processed=True).order_by("-pk")

        if not self.request.user.is_authenticated:
            video_results = video_results.filter(public=True)

        # query from the search bar
        search = self.request.GET.get('search', None)
        if search:
            video_results = video_results.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(collections__title__icontains=search)
            )

        return video_results

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        video_results = context['videos']
        collection_request = self.kwargs.get('collection', None)

        collections = VideoCollection.objects.order_by("?")
        if not self.request.user.is_authenticated:
            # if user is not authenticated, only show public videos and connected collections
            collection_pks = video_results.values_list('collections', flat=True)
            collections = collections.filter(id__in=collection_pks)

        if collection_request:
            requested = collections.filter(slug=collection_request)
            if requested:
                collections = list(collections.filter(slug=collection_request)) + list(collections.exclude(pk__in=requested).order_by('-title')[0:4])
            else:
                collections = collections[0:4]
        else:
            collections = collections.order_by('-title')

        context['collections'] = collections
        context['collection'] = collection_request
        context['search'] = self.request.GET.get('search', "")
        return context


class VideoDetailView(DetailView):
    model = Video
    queryset = Video.objects.filter(processed=True)

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


class VideoPlayerView(VideoDetailView):
    template_name = 'video/video_player.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs.get('slug')

        try:
            video = self.queryset.get(slug=slug)
        except Video.DoesNotExist:
            return context

        # get collections that video is in
        context['in_collections'] = VideoCollectionOrder.objects.filter(video=video)

        # get suggested next videos
        context['next_videos'] = []
        for vcn in context['in_collections']:
            next_in = VideoCollectionOrder.objects.filter(
                collection=vcn.collection,
                video__processed=True,
                order__gt=vcn.order,
            )

            if next_in:
                context['next_videos'].append(next_in.first())

        # get download options
        context['download_options'] = []
        for i, resolution in enumerate(RESOLUTIONS):
            context['download_options'].append({'resolution': resolution, 'value': i})
        context['download_options'].reverse()

        # playback location
        if self.request.user.is_authenticated:
            vpt, created = VideoPlaybackTracker.objects.get_or_create(
                user=self.request.user,
                video=video
            )
            context['seconds'] = vpt.seconds

        return context


class GetVideoFileView(VideoDetailView):
    """
    Abstract view class to retreive a file for a specific video. Subclasses should
    implement the get_filename() function and this class contains all other code to
    reply to the request with that file.
    """
    def get_filename(self):
        """
        This function needs to be implemented by subclasses.
        """
        raise HttpResponseServerError()

    def get(self, request, *args, **kwargs):
        path = os.path.join(settings.MEDIA_ROOT, self.get_filename())

        return sendfile(request, path)


class GetVideoThumbnailView(GetVideoFileView):
    # thumbnails can be accesed before video is fully processed
    queryset = Video.objects.all()

    def get_filename(self):
        return self.get_object().thumbnail.name


class GetVideoGifPreviewView(GetVideoFileView):
    # preview can be accesed before video is fully processed
    queryset = Video.objects.all()

    def get_filename(self):
        return self.get_object().gif_preview.name


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


@method_decorator(require_POST, name='dispatch')
@method_decorator(auth_or_404, name='dispatch')
class TrackPlaybackView(VideoDetailView):
    def post(self, request, *args, **kwargs):
        video = self.get_object()

        try:
            seconds = int(request.POST.get('seconds', None))
        except:
            return HttpResponseBadRequest()

        vpt, created = VideoPlaybackTracker.objects.get_or_create(
            user=request.user,
            video=video
        )

        # reset if 90% of the video has been played
        if seconds > video.duration * .9:
            vpt.seconds = 0
        else:
            vpt.seconds = seconds

        vpt.save()

        return JsonResponse({}, status=200)


@method_decorator(require_POST, name='dispatch')
@method_decorator(auth_or_404, name='dispatch')
class DownloadVideoView(VideoDetailView):
    def post(self, request, *args, **kwargs):
        video = self.get_object()
        try:
            resolution = int(request.POST.get('resolution', None)[0])
        except:
            return HttpResponseBadRequest()

        # audio only variant
        audio_variant = video.variants.all().order_by('-resolution')[0]
        try:
            # selected video quality variant
            video_variant = video.variants.get(resolution=resolution)
        except VideoVariant.DoesNotExist:
            raise HttpResponseServerError()

        video_filepath = os.path.join(settings.MEDIA_ROOT, video_variant.video_file.name)
        audio_filepath = os.path.join(settings.MEDIA_ROOT, audio_variant.video_file.name)

        # combine audio with video and pipe to variable for transmission
        command = \
            f'ffmpeg -v quiet -i {video_filepath} -i {audio_filepath} ' \
            f'-map 0:v:0 -map 1:a:0 -c copy -f matroska -'

        file_data = subprocess.check_output(shlex.split(command))

        response = HttpResponse(file_data, content_type="video/x-matroska")
        response['Content-Disposition'] = f'inline; filename={video.title}.mkv'

        return response


@method_decorator(auth_or_404, name='dispatch')
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


@method_decorator(auth_or_404, name='dispatch')
class VideoFormView(TemplateView):
    template_name = 'video/upload_form.html'

    def get(self, request, *args, **kwargs):
        slug = self.kwargs.get('slug', None)

        if slug:
            try:
                video = Video.objects.get(user=request.user, slug=slug)
                form = VideoUploadForm(instance=video)
            except Video.DoesNotExist:
                messages.add_message(request, messages.ERROR, 'Something went wrong. Try again later.')
                return redirect('user_uploads')
        else:
            form = VideoUploadForm()

        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = VideoUploadForm(request.POST)

        if form.is_valid():

            upload_id = form.cleaned_data.get('upload_id')
            try:
                video = Video.objects.get(user=request.user, upload_id=upload_id)
            except Video.DoesNotExist:
                video = Video(user=request.user)

            form = VideoUploadForm(request.POST, instance=video)

            vid = form.save()

            if self.request.is_ajax():
                return JsonResponse({}, status=201)
            else:
                messages.add_message(request, messages.SUCCESS, f'{vid.title} updated successfully!')
                return redirect('user_uploads')
        else:
            return JsonResponse(form.errors, status=400)


@method_decorator(auth_or_404, name='dispatch')
class EditVideoCollectionView(TemplateView):
    template_name = 'video/manage_collection.html'

    def get(self, request, *args, **kwargs):
        collection_slug = kwargs.get('slug', None)
        if not collection_slug:
            first = VideoCollection.objects.first()
            return redirect('collection_edit', slug=first.slug)

        video_results = VideoCollectionOrder.objects.filter(
            collection__slug=collection_slug
        )
        collections = VideoCollection.objects.all()

        payload = {
            'results': video_results,
            'collections': collections,
            'target': collection_slug
        }

        return render(request, self.template_name, payload)

    def post(self, request, *args, **kwargs):
        slugs = request.POST.getlist('slugs[]', None)
        target = request.POST.get('target', None)

        if not slugs or not target:
            return JsonResponse({}, status=500)

        # get all requested vcns
        try:
            vcns = VideoCollectionOrder.objects.select_for_update().filter(
                collection__slug=target,
                video__slug__in=slugs,
            )
        except VideoCollectionOrder.DoesNotExist:
            return JsonResponse({}, status=500)

        # reorder selected vcns
        try:
            with transaction.atomic():
                for i, slug in enumerate(slugs):
                    vcn = vcns.get(video__slug=slug)
                    # reorder all videos in collection
                    vcn.bottom()
        except DatabaseError:
            return JsonResponse({}, status=500)

        return JsonResponse({}, status=200)


@method_decorator(auth_or_404, name='dispatch')
class EditVideoView(VideoFormView):
    template_name = 'video/edit_form.html'


@method_decorator(auth_or_404, name='dispatch')
class DeleteVideoView(View):
    def get(self, request, *args, **kwargs):
        slug = self.kwargs.get('slug', None)

        if not slug:
            messages.add_message(request, messages.ERROR, 'Something went wrong. Try again later.')

        try:
            video = Video.objects.get(slug=slug, user=request.user, processed=True)
            messages.add_message(request, messages.INFO, f'{video.title} deleted.')
            video.delete()
        except Video.DoesNotExist:
            messages.add_message(request, messages.ERROR, 'Something went wrong. Try again later.')

        return redirect('user_uploads')


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

        vid.begin_processing()

        return JsonResponse({})


    def get_response_data(self, chunked_upload, request):
        return {'message': ("You successfully uploaded '%s' (%s bytes)!" %
(chunked_upload.filename, chunked_upload.offset))}

