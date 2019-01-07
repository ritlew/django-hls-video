from django.urls import path
from django.views.generic.base import RedirectView

from . import views

favicon_view = RedirectView.as_view(url='/static/home/image/favicon.ico', permanent=True)

urlpatterns = [
    path('', views.blog_index, name="blog_index"),
    path('<slug:requested_slug>/', views.blog_detail, name='blog_detail'),
]