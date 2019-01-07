from django.shortcuts import render

from .models import BlogEntry

from itertools import zip_longest


def blog_index(request):
    blog_entries = BlogEntry.objects.all().order_by('-date_created')
    return render(request, "blog/index.html", {'entries': blog_entries})


def blog_detail(request, requested_slug):
    blog_entry = BlogEntry.objects.get(url_slug=requested_slug)
    return render(request, "blog/blog_detail.html", {'blog_entry': blog_entry})
