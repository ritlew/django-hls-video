# Generated by Django 2.2.2 on 2019-10-12 23:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0004_videoplaybacktracker'),
    ]

    operations = [
        migrations.RenameField(
            model_name='videoplaybacktracker',
            old_name='location',
            new_name='seconds',
        ),
    ]
