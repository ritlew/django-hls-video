from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.VideoListView.as_view(), name="video_index"),
    path('s/<collection>/', views.VideoListView.as_view(), name="video_index"),
    path('get/<slug:slug>/', include([
        path('thumbnail/', views.GetVideoThumbnailView.as_view(), name="get_thumbnail"),
        path('master_playlist/', include([
            path('', views.GetMasterPlaylistView.as_view(), name="get_master_playlist"),
            path('<int:variant>.m3u8', views.GetVariantPlaylistView.as_view(), name="get_variant_playlist"),
            path('<int:variant>.m4s', views.GetVariantVideoView.as_view(), name="get_video"),
        ])),
    ])),
    path('play/<slug:slug>/', views.VideoPlayerView.as_view(), name="video_player"),
    path('upload/', views.VideoFormView.as_view(), name="video_form"),
    path('edit/<slug:slug>/', views.EditVideoView.as_view(), name="edit_video"),
    path('delete/<slug:slug>/', views.DeleteVideoView.as_view(), name="delete_video"),
    path('uploads/', views.UserUploadsView.as_view(), name="user_uploads"),
    path('api/colleciton_autocomplete/', views.CollectionAutocomplete.as_view(create_field='title'), name='api_collection_autocomplete'),
    path('video_file_upload/', include([
        path('', views.VideoChunkedUploadView.as_view(), name='video_chunked_upload'),
        path('complete/', views.VideoChunkedUploadCompleteView.as_view(), name='video_chunked_upload_complete'),
    ])),
]
