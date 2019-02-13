from django.http import JsonResponse
from django.shortcuts import render

import json

from chunked_upload.views import ChunkedUploadView, ChunkedUploadCompleteView

from .forms import UploadModelForm
from .models import VideoFile, MyChunkedUpload
from .tasks import process_video_file


def video_index(request):
    vids = VideoFile.objects.filter(processed=True).order_by("-pk")[:10]
    return render(request, "video/index.html", {"videos": vids})

def video_player(request, vid_pk=0):
    vid_object = VideoFile.objects.get(pk=vid_pk)
    
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
        # Do something with the uploaded file. E.g.:
        # * Store the uploaded file on another model:
        # SomeModel.objects.create(user=request.user, file=uploaded_file)
        # * Pass it as an argument to a function:
        # function_that_process_file(uploaded_file)
        vid = VideoFile.objects.get(upload_id=request.POST.get("upload_id"))
        vid.raw_video_file = uploaded_file
        vid.upload_id = None
        vid.save()
        process_video_file.delay(vid.pk)
        return JsonResponse({"message": "file upload success"})
        

    def get_response_data(self, chunked_upload, request):
        return {'message': ("You successfully uploaded '%s' (%s bytes)!" %
(chunked_upload.filename, chunked_upload.offset))}
