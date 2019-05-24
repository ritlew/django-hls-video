import os
import django
from channels.routing import get_default_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_hls_video.settings")
django.setup()
application = get_default_application()
