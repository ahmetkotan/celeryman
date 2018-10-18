from celery.task.control import inspect, revoke
from celery.execute import send_task

from celeryman.exceptions import TaskNotFoundError

import datetime

def start_celery_task(task):
    from celeryman.models import ManagedTask

    task_args = task.celery_task_args
    task_name = task.get_celery_task_full_name()

    is_exists = ManagedTask.objects.filter(
        task=task.task,
        celery_task_args=task_args,
        celery_task_status=1,
        is_enable=True
    )
    if is_exists.exists():
        task.celery_task_status = 6
        task.is_enable = False
        task.save(check_enable=False)
    else:
        task.is_enable = True
        task.save(check_enable=False)

        celery_task = task.task
        celery_task.last_run = datetime.datetime.now()
        celery_task.save()

        send_task(task_name, task.get_task_args())


def stop_celery_task(task):
    if not task.celery_task_id:
        raise TaskNotFoundError("This task is not found.")

    active_list = get_active_task_id_list()
    if task.celery_task_id in active_list:
        task.celery_task_status = 5
        task.save(check_enable=False)

        revoke(task.celery_task_id, terminate=True, signal='SIGTERM')
        return True
    else:
        raise TaskNotFoundError("This task is not fund.")



def get_active_task_id_list():
    i = inspect()
    task_id_list = []

    active_tasks = i.active()

    if active_tasks:
        for _, tasks in active_tasks.items():
            for task in tasks:
                task_id_list.append(task['id'])

    return task_id_list
