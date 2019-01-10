from django.http import HttpResponse
from django.shortcuts import render

import json

from .forms import UploadModelForm
from .models import VideoFile
from .tasks import process_video_file


def video_index(request):
    vid_object = VideoFile.objects.latest('pk')
    
    if not vid_object.processed:
        process_video_file.delay(vid_object.pk)

    return render(request, "video/video_index.html")

def video2(request):
    return render(request, "video/video2.html")

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

