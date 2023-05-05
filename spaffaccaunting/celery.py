from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spaffaccaunting.settings')

app = Celery('spaffaccaunting')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    'import_transactions': {
        'task': 'mainapp.tasks.import_transactions',
        'schedule': crontab(hour='*/1'),
        'args': ()
    }
}

app.autodiscover_tasks()
