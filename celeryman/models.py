from django.db import models
from django.core.exceptions import ValidationError


import json

# Create your models here.

from celeryman.validators import task_name_validator, task_args_validator
from celeryman.utils import start_celery_task, stop_celery_task


class CeleryTask(models.Model):
    task_full_name = models.CharField(
        max_length=250,
        verbose_name='Celery Task Full Name'
    )

    task_name = models.CharField(
        max_length=60,
        verbose_name='Celery Task Name'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Is task active?'
    )

    last_run = models.DateTimeField(
        auto_now_add=False,
        auto_now=False,
        null=True, blank=True
    )

    def __str__(self):
        return self.task_full_name

    def __unicode__(self):
        return self.task_full_name

    task_args = None
    def set_task_args(self, value):
        self.task_args = task_args_validator(value)

    def start(self):
        if not self.task_args:
            self.task_args = []

        m = ManagedTask.objects.create(
            task=self,
            celery_task_args=self.task_args,
            is_enable=True,
        )
        return m

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.task_name = self.task_full_name.split(".")[-1]
        super(CeleryTask, self).save()


    class Meta:
        verbose_name = 'Usable Celery Task'
        verbose_name_plural = 'Usable Celery Tasks'

class ManagedTask(models.Model):
    TASK_STATUSES = (
        (0, 'PENDING'),
        (1, 'STARTED'),
        (2, 'RETRY'),
        (3, 'FAILURE'),
        (4, 'SUCCESS'),
        (5, 'REVOKED'),
        (6, 'REJECTED'),
        (7, 'CRASHED')
    )

    task = models.ForeignKey(
        CeleryTask,
        related_name='celerytask_task',
        null=True, blank=True
    )

    task_name = models.CharField(
        max_length=60,
        verbose_name='Celery Task Name',
        null=True, blank=True,
        validators=[task_name_validator],
    )

    celery_task_id = models.CharField(
        max_length=36,
        verbose_name='Celery Task ID',
        null=True, blank=True,
    )

    celery_task_args = models.TextField(
        verbose_name='Celery Task Args',
        null=True, blank=True,
        validators=[task_args_validator],
        default=[]
    )

    celery_task_status = models.IntegerField(
        choices=TASK_STATUSES,
        default=0,
    )

    is_enable = models.BooleanField(
        default=False,
        verbose_name='Enable?'
    )

    created_time = models.DateTimeField(
        auto_now_add=True,
        auto_now=False
    )

    manual = models.BooleanField(
        default=True,
        verbose_name='Manual trigged'
    )

    def start(self):
        start_celery_task(self)

    def stop(self):
        stop_celery_task(self)

    def get_celery_task_name(self):
        return self.task.task_name

    def get_celery_task_full_name(self):
        return self.task.task_full_name

    def get_celery_task(self):
        return CeleryTask.objects.get(task_name=self.task_name)

    def set_task_args(self, value):
        self.celery_task_args = task_args_validator(value)
        self.save(set_function=True)

    def get_task_args(self):
        return json.loads(self.celery_task_args)

    def enabled_check(self):
        status = {
            'enabled': 1,
            'disabled': 2,
            'nop': 3,
        }

        if self.id is None:
            if self.is_enable == True:
                return status['enabled']
            else:
                return status['nop']

        old_self = ManagedTask.objects.get(id=self.id)
        if old_self.is_enable == False and self.is_enable == True:
            return status['enabled']
        elif old_self.is_enable == True and self.is_enable == False:
            return status['disabled']
        else:
            return status['nop']

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None, set_function=None, check_enable=True):

        if not self.task and not self.task_name:
            raise ValidationError("You must enter Celery Task object for task field or task_name.")

        self.full_clean()

        if not self.task and self.task_name:
            self.task = self.get_celery_task()

        if self.task and not self.task_name:
            self.task_name = self.task.task_name

        if not set_function:
            self.celery_task_args = task_args_validator(self.celery_task_args)

        if check_enable:
            operation = self.enabled_check()
            if operation == 1 and self.manual == True:
                self.start()
            elif operation == 2 and self.manual == True:
                self.stop()


        if self.celery_task_status == 1:
            self.is_enable = True

        if self.celery_task_status in [3, 4, 5, 6]:
            self.is_enable = False

        super(ManagedTask, self).save()


    def __str__(self):
        return "%s:%s" % (self.task_name, self.celery_task_args)

    def __unicode__(self):
        return "%s:%s" % (self.task_name, self.celery_task_args)


    class Meta:
        verbose_name = 'Managed Celery Task'
        verbose_name_plural = 'Managed Celery Tasks'
