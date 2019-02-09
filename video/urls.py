from django.urls import path

from . import views

urlpatterns = [
    path('', views.video_index, name="video_index"),
    path('2', views.video2, name="video2"),
    path('form', views.form_view, name="video_form"),
]
