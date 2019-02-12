from django.http import HttpResponse
from django.shortcuts import render

import json

from chunked_upload.views import ChunkedUploadView, ChunkedUploadCompleteView

from .forms import UploadModelForm
from .models import VideoFile, MyChunkedUpload
from .tasks import process_video_file


def video_index(request):
    vid_object = VideoFile.objects.latest('pk')
    
    if not vid_object.processed:
        return render(request, "video/video_index.html")

    return render(request, "video/video_index.html", {"vid": vid_object})

def form_view(request):
    if request.method == 'POST':
        form = UploadModelForm(request.POST, request.FILES)
        if form.is_valid():
            vid = form.save()
            process_video_file.delay(vid.pk)
            return HttpResponse(json.dumps({"message": "ok"}))
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
        pass

    def get_response_data(self, chunked_upload, request):
        return {'message': ("You successfully uploaded '%s' (%s bytes)!" %
(chunked_upload.filename, chunked_upload.offset))}
