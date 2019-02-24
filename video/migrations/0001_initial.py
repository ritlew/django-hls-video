# Generated by Django 2.0.6 on 2019-02-24 19:09

import chunked_upload.models
import chunked_upload.settings
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MyChunkedUpload',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('upload_id', models.CharField(default=chunked_upload.models.generate_upload_id, editable=False, max_length=32, unique=True)),
                ('file', models.FileField(max_length=255, upload_to=chunked_upload.settings.default_upload_to)),
                ('filename', models.CharField(max_length=255)),
                ('offset', models.BigIntegerField(default=0)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('status', models.PositiveSmallIntegerField(choices=[(1, 'Uploading'), (2, 'Complete')], default=1)),
                ('completed_on', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='chunked_uploads', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='VideoFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=50)),
                ('header', models.CharField(max_length=50, null=True)),
                ('description', models.TextField()),
                ('upload_id', models.CharField(max_length=50, null=True)),
                ('raw_video_file', models.FileField(null=True, upload_to='video/')),
                ('processed', models.BooleanField(default=False)),
                ('mpd_file', models.FilePathField(default=None, null=True)),
                ('thumbnail', models.FilePathField(default=None, null=True)),
                ('task_id', models.CharField(max_length=50)),
            ],
        ),
    ]
