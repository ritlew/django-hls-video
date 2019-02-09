"""
WSGI config for ritlew project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ritlew.settings")
#os.environ.setdefault("DJANGO_SETTINGS", "production")

application = get_wsgi_application()
