# Django imports
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.views.generic.base import View, TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.utils.decorators import method_decorator
from django.http import (
    HttpResponse, JsonResponse, Http404, HttpResponseBadRequest, HttpResponseServerError
)

# Python standard imports
import json
import os

# third-party imports
from celery import group
from chunked_upload.views import ChunkedUploadView, ChunkedUploadCompleteView
from dal import autocomplete
from sendfile import sendfile

# local imports
from .forms import VideoUploadForm, VideoCollectionNumberForm
from .models import Video, VideoCollection, VideoChunkedUpload

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


@method_decorator(login_required, name='dispatch')
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


@method_decorator(login_required, name='dispatch')
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
                form = VideoUploadForm(request.POST, instance=video)
            except Video.DoesNotExist:
                form = VideoUploadForm(request.POST)

            vid = form.save(commit=False)
            vid.user = request.user
            vid.save()
            form.save_m2m()

            if self.request.is_ajax():
                return JsonResponse({}, status=201)
            else:
                messages.add_message(request, messages.SUCCESS, f'{vid.title} updated successfully!')
                return redirect('user_uploads')
        else:
            return JsonResponse(form.errors, status=400)


@method_decorator(login_required, name='dispatch')
class VideoCollectionNumberFormView(TemplateView):
    template_name = 'video/edit_form.html'

    def get(self, request, *args, **kwargs):
        form = VideoCollectionNumberForm()

        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = VideoCollectionNumberForm(request.POST)

        if form.is_valid():
            form.save()

            if self.request.is_ajax():
                return JsonResponse({}, status=201)
            else:
                messages.add_message(request, messages.SUCCESS, 'Collection updated successfully!')
                return redirect('user_uploads')
        else:
            return render(request, self.template_name, {'form': form})


@method_decorator(login_required, name='dispatch')
class EditVideoView(VideoFormView):
    template_name = 'video/edit_form.html'


@method_decorator(login_required, name='dispatch')
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


class VideoAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Video.objects.none()

        queryset = Video.objects.all().order_by('title')

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

