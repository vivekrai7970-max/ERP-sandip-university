import os
import sys
import django

# Add the sandip_university directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sandip_university'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sandip_university.settings')
django.setup()

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

