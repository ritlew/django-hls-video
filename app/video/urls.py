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
    path('download/<slug:slug>/', views.DownloadVideoView.as_view(), name="download_video"),
    path('uploads/', views.UserUploadsView.as_view(), name="user_uploads"),
    path('collection/', include([
        path('edit/', views.EditVideoCollectionView.as_view(), name='collection_edit'),
        path('edit/<slug>/', views.EditVideoCollectionView.as_view(), name='collection_edit'),
    ])),
    path('api/autocomplete/', include([
        path(
            'video/',
            views.VideoAutocomplete.as_view(),
            name='autocomplete_video'
        ),
        path(
            'collection/',
            views.CollectionAutocomplete.as_view(create_field='title'),
            name='autocomplete_collection'
        ),
    ])),
    path('video_file_upload/', include([
        path('', views.VideoChunkedUploadView.as_view(), name='video_chunked_upload'),
        path('complete/', views.VideoChunkedUploadCompleteView.as_view(), name='video_chunked_upload_complete'),
    ])),
]
