from django.conf.urls import url, include
from . import views


urlpatterns = [
    url(r'^$', views.index, name="index"),
    url(r'^video/$', views.video, name="video"),
    url(r'^music/$', views.music, name="music"),
    url(r'^blog/', include("blog.urls")),
]

