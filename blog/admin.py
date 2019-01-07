from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from .models import BlogEntry


class BlogAdmin(SummernoteModelAdmin):
    prepopulated_fields = {"url_slug": ("title",)}
    summernote_fields = ('body',)


admin.site.register(BlogEntry, BlogAdmin)
