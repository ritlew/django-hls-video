from __future__ import absolute_import
import os
from celery import Celery
from celery.signals import beat_init
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_hls_video.settings')
app = Celery('django_hls_video')

@beat_init.connect
def at_start(sender, **kwargs):
    with sender.app.connection() as conn:
        sender.app.send_task('video.tasks.startup_task', connection=conn)

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.task_routes = {'video.tasks.create_variants': {'queue': 'encoding_queue'}}
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

