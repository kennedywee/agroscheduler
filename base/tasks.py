# from __future__ import absolute_import, unicode_literals

# from celery import shared_task

# from celery.schedules import crontab

# import datetime

# from datetime import datetime

# import requests

# import time

# import pytz


# @shared_task
# def add(x, y):
#     time.sleep(5)
#     return x + y


# @shared_task
# def send_mail(email):
#     print(f'Sending mail to {email}...')


# @shared_task
# def fetch_schedule_list_task():
#     print('Fetching schedule list...')
#     response = requests.get(
#         'http://127.0.0.1:8000/api/schedules/agroscheduler/')
#     schedule_list = response.json()
#     assigned_tasks = []

#     for schedule in schedule_list:

#         import datetime
#         import json
#         datetime_obj = datetime.datetime.now(datetime.timezone.utc)
#         datetime_str = datetime_obj.isoformat()

#         # Serialize the datetime string to JSON
#         serialized_data = json.dumps({'datetime': datetime_str})

#         # Deserialize the JSON data back to a datetime object
#         deserialized_data = json.loads(serialized_data)
#         datetime_str = deserialized_data['datetime']
#         datetime_obj = datetime.datetime.fromisoformat(datetime_str)

#         if task_id in assigned_tasks:
#             continue

#         print("Assigning schedule to celery beat...")
#         schedule_duration = schedule['duration']
#         perform_schedule_task.apply_async(
#             args=[schedule['id'], schedule_duration, schedule['device'], schedule['field'], ], eta=datetime_obj.replace(microsecond=0), timezone=pytz.UTC)
#         assigned_tasks.append(task_id)


# @shared_task
# def perform_schedule_task(schedule_id, schedule_duration, device, field):

#     import datetime

#     print(f'Performing schedule {schedule_id}.. {schedule_duration}.')

# request_link = "http://127.0.0.1:8000/api/data/agroscheduler/{}/?{}={}"
# response = requests.get(request_link.format(device, field, 1.0))

#     # wait for the duration of the schedule
#     duration = datetime.datetime.strptime(
#         schedule_duration, "%H:%M:%S") - datetime.datetime.strptime("00:00:00", "%H:%M:%S")
#     sleep_duration = duration.total_seconds()
#     print(sleep_duration)
#     time.sleep(sleep_duration)

#     request_link = "http://127.0.0.1:8000/api/data/agroscheduler/{}/?{}={}"
#     response = requests.get(request_link.format(device, field, 0.0))

import requests
from celery import shared_task
from celery.result import AsyncResult
import traceback
from .models import Schedule, ScheduleTaskState
from django.conf import settings
from django.core.mail import send_mail
import time


@shared_task
def perform_schedule_task(id, duration, device, field):

    request_link = "http://127.0.0.1:8000/api/data/agroscheduler/{}/?{}={}"
    response = requests.get(request_link.format(device, field, 1.0))
    print("response: ", response.json())

    time.sleep(duration)

    request_link = "http://127.0.0.1:8000/api/data/agroscheduler/{}/?{}={}"
    response = requests.get(request_link.format(device, field, 0.0))

    print("response: ", response.json())

    schedule = Schedule.objects.get(custom_id=id)
    schedule.active = False
    schedule.save()


@shared_task
def schedule_task():
    schedules = Schedule.objects.filter(active=True)

    for schedule in schedules:

        task_id = schedule.custom_id

        task_scheduled = ScheduleTaskState.objects.filter(
            task_id=task_id).exists()
        if task_scheduled:
            # print("Task already scheduled.")
            continue

        duration_seconds = schedule.duration.total_seconds()

        result = perform_schedule_task.apply_async(eta=schedule.datetime, args=[
            schedule.custom_id, duration_seconds, schedule.device, schedule.field, ], task_id=task_id)

        state = ScheduleTaskState.objects.create(
            task_id=task_id, state=result.state)
        state.save()


@shared_task
def fetch_schedule_list_task():
    print('Fetching schedule list...')
    response = requests.get(
        'http://127.0.0.1:8000/api/schedules/agroscheduler/')

    schedule_list = response.json()

    for item in schedule_list:
        id = item['id']
        if Schedule.objects.filter(custom_id=id).exists():
            # print('Schedule already exists in database.')
            continue

        try:
            schedule = Schedule(
                custom_id=item['id'],
                name=item['name'],
                datetime=item['datetime'],
                duration=item['duration'],
                field=item['field'],
                active=item['active'],
                user=item['user'],
                device=item['device'],
            )
            schedule.save()
            # print('Schedule saved to database.')

        except Exception as e:
            print("An error occurred:")
            print(traceback.format_exc())
