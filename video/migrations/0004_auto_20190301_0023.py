# Generated by Django 2.0.6 on 2019-03-01 00:23

import autoslug.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0003_auto_20190301_0016'),
    ]

    operations = [
        migrations.AlterField(
            model_name='videoupload',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=False, populate_from='title', unique=True),
        ),
    ]