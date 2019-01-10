from django.urls import path

from . import views

urlpatterns = [
   path('', views.video_index, name="video_index"),
]
