import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sandip_university.settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
