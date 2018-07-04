from django.shortcuts import render

# Create your views here.


def index(request):
    return render(request, 'home/index.html')


def video(request):
    return render(request, 'home/video.html')


def music(request):
    return render(request, 'home/music.html')
