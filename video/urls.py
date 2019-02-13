from django.urls import path

from . import views

urlpatterns = [
    path('', views.video_index, name="video_index"),
    path('play/<int:vid_pk>/', views.video_player, name="video_player"),
    path('form', views.form_view, name="video_form"),
    path('api/chunked_upload/', views.MyChunkedUploadView.as_view(), name='api_chunked_upload'),
    path('api/chunked_upload_complete/', views.MyChunkedUploadCompleteView.as_view(), name='api_chunked_upload_complete'),
]
