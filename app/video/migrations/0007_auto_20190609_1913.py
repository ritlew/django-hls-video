# Generated by Django 2.2.2 on 2019-06-09 19:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0006_auto_20190608_2202'),
    ]

    operations = [
        migrations.AlterField(
            model_name='video',
            name='description',
            field=models.TextField(default=''),
        ),
    ]
