import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openrecruit.settings')

app = Celery('openrecruit')
app.config_from_object('django.conf:settings', namespace='celery')
app.autodiscover_tasks()
