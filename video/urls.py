from django.urls import path

from . import views

urlpatterns = [
    path('', views.video_index, name="video_index"),
    path('form', views.form_view, name="video_form"),
    path('api/chunked_upload/', views.MyChunkedUploadView.as_view(), name='api_chunked_upload'),
    path('api/chunked_upload_complete/', views.MyChunkedUploadCompleteView.as_view(), name='api_chunked_upload_complete'),
]
