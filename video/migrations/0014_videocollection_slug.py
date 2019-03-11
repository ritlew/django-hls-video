# Generated by Django 2.0.6 on 2019-03-11 00:00

import autoslug.fields
from django.db import migrations
from django.utils.text import slugify


class Migration(migrations.Migration):
    def forward_func(apps, schema_editor):
        VideoCollection = apps.get_model("video", "VideoCollection")
        for instance in VideoCollection.objects.all():
            if not instance.slug:
                instance.slug = slugify(instance.name)
                instance.save()

    def reverse_func(apps, schema_editor):
        pass

    dependencies = [
        ('video', '0013_auto_20190310_2326'),
    ]

    operations = [
        migrations.AddField(
            model_name='videocollection',
            name='slug',
            field=autoslug.fields.AutoSlugField(default='', editable=False, populate_from='title', unique=True),
            preserve_default=False,
        ),
        migrations.RunPython(forward_func, reverse_func)
    ]
