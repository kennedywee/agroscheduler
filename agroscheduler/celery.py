import os

from celery import Celery
from celery.schedules import crontab


# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agroscheduler.settings')
os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1')

app = Celery('agroscheduler')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')


app.conf.beat_schedule = {
    # Periodic check schedule list and add to database
    'fetch-schedule-list': {
        'task': 'base.tasks.fetch_schedule_list_task',
        'schedule': 15,
    },
    'schedule-task': {
        'task': 'base.tasks.schedule_task',
        'schedule': 30,
    }
}

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
