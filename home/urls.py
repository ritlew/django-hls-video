from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic.base import RedirectView

from . import views

favicon_view = RedirectView.as_view(url='/static/home/image/favicon.ico', permanent=True)

urlpatterns = [
    url(r'^$', views.index, name="index"),
    url(r'^favicon\.ico$', favicon_view),
    url(r'^video/$', views.video, name="video"),
    url(r'^music/$', views.music, name="music"),
]

