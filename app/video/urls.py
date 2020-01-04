from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.VideoListView.as_view(), name="video_index"),
    path('collection/<collection>/', views.VideoListView.as_view(), name="video_index"),
    path('tag/<tag>/', views.VideoListView.as_view(), name="video_index"),
    path('videos/<slug:slug>/', include([
        path('play/', views.VideoPlayerView.as_view(), name="video_player"),
        path('edit/', views.EditVideoView.as_view(), name="edit_video"),
        path('delete/', views.DeleteVideoView.as_view(), name="delete_video"),
        path('download/', views.DownloadVideoView.as_view(), name="download_video"),
        path('thumbnail/', views.GetVideoThumbnailView.as_view(), name="get_thumbnail"),
        path('gif/', views.GetVideoGifPreviewView.as_view(), name="get_gif_preview"),
        path('track_playback/', views.TrackPlaybackView.as_view(), name="track_playback"),
        path('master_playlist/', include([
            path('', views.GetMasterPlaylistView.as_view(), name="get_master_playlist"),
            path('<int:variant>.m3u8', views.GetVariantPlaylistView.as_view(), name="get_variant_playlist"),
            path('<int:variant>.m4s', views.GetVariantVideoView.as_view(), name="get_video"),
        ])),
    ])),
    path('upload/', views.VideoFormView.as_view(), name="video_form"),
    path('uploads/', views.UserUploadsView.as_view(), name="user_uploads"),
    path('collections/', include([
        path('edit/', views.EditVideoCollectionView.as_view(), name='collection_edit'),
        path('<slug:slug>/edit/', views.EditVideoCollectionView.as_view(), name='collection_edit'),
    ])),
    path('api/autocomplete/', include([
        path(
            'collection/',
            views.CollectionAutocomplete.as_view(create_field='title'),
            name='autocomplete_collection'
        ),
        path(
            'tag/',
            views.TagAutocomplete.as_view(create_field='title'),
            name='autocomplete_tag'
        ),
    ])),
    path('video_file_upload/', include([
        path('', views.VideoChunkedUploadView.as_view(), name='video_chunked_upload'),
        path('complete/', views.VideoChunkedUploadCompleteView.as_view(), name='video_chunked_upload_complete'),
    ])),
]
