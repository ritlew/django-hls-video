# Generated by Django 2.0.6 on 2019-03-07 02:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0008_auto_20190307_0218'),
    ]

    operations = [
        migrations.RenameField(
            model_name='video',
            old_name='upload_info',
            new_name='upload',
        ),
    ]