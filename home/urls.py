from django.urls import path, include
from . import views


urlpatterns = [
    path('', views.index, name="index"),
    path('video/', include("video.urls")),
    path('music/', views.music, name="music"),
    path('blog/', include("blog.urls")),
]
