from django.db import models
from datetime import timedelta


class Schedule(models.Model):
    custom_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    datetime = models.DateTimeField()
    duration = models.DurationField()
    field = models.CharField(max_length=100)
    active = models.BooleanField()
    user = models.PositiveIntegerField()
    device = models.PositiveIntegerField()

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if type(self.duration) == str:
            self.duration = timedelta(hours=int(self.duration.split(':')[0]),
                                      minutes=int(self.duration.split(':')[1]),
                                      seconds=int(self.duration.split(':')[2]))
        super().save(*args, **kwargs)


class ScheduleTaskState(models.Model):
    task_id = models.CharField(max_length=255, unique=True)
    state = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
