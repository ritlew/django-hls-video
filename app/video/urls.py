from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.VideoListView.as_view(), name="video_index"),
    path('s/<collection>/', views.VideoListView.as_view(), name="video_index"),
    path('process/<int:vid_pk>/', views.process_video, name='process_video'),
    path('get/<slug:slug>/', include([
        path('thumbnail/', views.GetVideoThumbnailView.as_view(), name="get_thumbnail"),
        path('master_playlist/', include([
            path('', views.GetMasterPlaylistView.as_view(), name="get_master_playlist"),
            path('<int:variant>.m3u8', views.GetVariantPlaylistView.as_view(), name="get_variant_playlist"),
            path('<int:variant>.m4s', views.GetVariantVideoView.as_view(), name="get_video"),
        ])),
    ])),
    path('play/<slug:slug>/', views.VideoPlayerView.as_view(), name="video_player"),
    path('upload/', views.SubmitVideoUpload.as_view(), name="video_form"),
    path('api/chunked_upload/', views.MyChunkedUploadView.as_view(), name='api_chunked_upload'),
    path('api/chunked_upload_complete/', views.MyChunkedUploadCompleteView.as_view(), name='api_chunked_upload_complete'),
    path('api/colleciton_autocomplete/', views.CollectionAutocomplete.as_view(create_field='title'), name='api_collection_autocomplete'),
]
