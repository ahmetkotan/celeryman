from celery.signals import (
    worker_ready, task_prerun, task_postrun,
    task_success, task_retry, task_failure,
    task_revoked, task_rejected, worker_shutting_down
)
from celery.task.control import revoke


from celeryman.models import CeleryTask, ManagedTask
from celeryman.exceptions import ExistingTaskError
from celeryman.validators import task_args_validator

import datetime

def on_worker_ready(*args, **kwargs):
    all_tasks = kwargs['sender'].task_buckets.keys()
    task_extractor = lambda x: not x.startswith('celery.')
    current_tasks = [i for i in filter(task_extractor, all_tasks)]

    existing_tasks = CeleryTask.objects.filter(is_active=True)
    active_tasks = CeleryTask.objects.filter(task_full_name__in=current_tasks)
    stopped_tasks = existing_tasks.difference(active_tasks)

    stopped_tasks.update(is_active=False)
    active_tasks.update(is_active=True)

    existing_task_list = CeleryTask.objects.values_list('task_full_name', flat=True)
    diff_tasks = set(current_tasks) - set(existing_task_list)
    for task_name in diff_tasks:
        CeleryTask.objects.create(task_full_name=task_name)

    crashed_tasks = ManagedTask.objects.filter(is_enable=True, celery_task_status=6)
    for task in crashed_tasks:
        task.celery_task_status = 7
        task.is_enable = False
        task.save()

        new_task = ManagedTask.objects.create(
            task=task.get_celery_task(),
            celery_task_args=task.get_task_args(),
        )
        new_task.start()



def on_task_prerun(*args, **kwargs):
    task = kwargs['task']

    task_id = task.request.id
    task_name = task.request.task
    task_args = task.request.args
    validate_args = task_args_validator(task_args)

    celery_task = CeleryTask.objects.get(task_full_name=task_name)
    is_exists = ManagedTask.objects.filter(
        task=celery_task,
        celery_task_args=validate_args,
        celery_task_status=1,
        is_enable=True,
        celery_task_id__isnull=False
    )
    if is_exists.exists():
        ManagedTask.objects.create(
            task=celery_task,
            celery_task_args=validate_args,
            celery_task_status=6,
            celery_task_id=task_id,
            is_enable=False,
            manual=False
        )
        revoke(task_id, terminate=True, signal='SIGTERM')
        raise ExistingTaskError("This task already exists with the same args.")
    else:
        is_exists2 = ManagedTask.objects.filter(
            task=celery_task,
            celery_task_args=validate_args,
            celery_task_status=0,
            is_enable=True
        )
        if is_exists2.exists():
            managed_task = is_exists2[0]
            managed_task.celery_task_id = task_id
            managed_task.celery_task_status = 1
            managed_task.is_enable = False
            managed_task.save(check_enable=False)
        else:
            celery_task.last_run = datetime.datetime.now()
            celery_task.save()
            ManagedTask.objects.create(
                task=celery_task,
                celery_task_args=validate_args,
                celery_task_status=1,
                celery_task_id=task_id,
                manual=False,
                is_enable=True,
            )


def on_task_finished(*args, **kwargs):
    task = kwargs['task']

    task_id = task.request.id

    task_status = task.AsyncResult(task.request.id).state
    task = ManagedTask.objects.get(celery_task_id=task_id)
    task.is_enable = False

    task.save(check_enable=False)


def on_task_success(*args, **kwargs):
    task = kwargs['sender']

    task_id = task.request.id
    task = ManagedTask.objects.get(celery_task_id=task_id)
    task.celery_task_status = 4
    task.is_enable = False
    task.save(check_enable=False)

def on_task_retry(*args, **kwargs):
    task = kwargs['sender']

    task_id = task.request.id
    task = ManagedTask.objects.get(celery_task_id=task_id)
    task.celery_task_status = 2
    task.is_enable = False
    task.save(check_enable=False)

def on_task_failure(*args, **kwargs):
    task = kwargs['sender']

    task_id = task.request.id
    task = ManagedTask.objects.get(celery_task_id=task_id)
    task.celery_task_status = 3
    task.is_enable = False
    task.save(check_enable=False)

def on_task_revoked(*args, **kwargs):
    task = kwargs['sender']

    task_id = task.request.id
    task = ManagedTask.objects.get(celery_task_id=task_id)
    task.celery_task_status = 5
    task.is_enable = False
    task.save(check_enable=False)

def on_task_rejected(*args, **kwargs):
    task = kwargs['sender']

    task_id = task.request.id
    task = ManagedTask.objects.get(celery_task_id=task_id)
    task.celery_task_status = 6
    task.is_enable = False
    task.save(check_enable=False)

def on_task_worker_shutting_down(*args, **kwargs):
    ManagedTask.objects.filter(is_enable=True).update(celery_task_status=6)


worker_ready.connect(on_worker_ready, dispatch_uid='on_worker_ready')
task_prerun.connect(on_task_prerun, dispatch_uid='on_task_prerun')
task_postrun.connect(on_task_finished, dispatch_uid='on_task_postrun')

task_success.connect(on_task_success, dispatch_uid='on_task_success')
task_retry.connect(on_task_retry, dispatch_uid='on_task_retry')
task_failure.connect(on_task_failure, dispatch_uid='on_task_failure')
task_revoked.connect(on_task_revoked, dispatch_uid='on_task_revoked')
task_rejected.connect(on_task_rejected, dispatch_uid='on_task_rejected')
worker_shutting_down.connect(on_task_worker_shutting_down, dispatch_uid='on_task_worker_shutting')