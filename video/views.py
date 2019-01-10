from django.shortcuts import render


def video_index(request):
    return render(request, "video/video_index.html")
