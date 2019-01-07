from django.db import models


class BlogEntry(models.Model):
    title = models.CharField(max_length=50)
    body = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    url_slug = models.SlugField()
