=====================================================================
 Celeryman
=====================================================================
Celeryman is a management application for celery async tasks on django.
It can manage created async tasks or you can create async task with ManagedTask or CeleryTask models.

  Task cannot be created with the same arguments at the same time.

Installation
============
on Pypi
::
  pip install celeryman
on Github
::
  git clone git@github.com:ahmetkotan/celeryman.git
  cd celeryman
  python setup.py install

Settings
============
After celery integration is completed, just add the celeryman app to `INSTALLED_APPS`.
::

  INSTALLED_APPS = [
      ...
      'celeryman',
      ...
  ]

About
=====
When celery service is run, Celeryman will discover tasks and save to database as CeleryTask object.
If you create async task with `apply_async()`, `delay()` etc. methods, Celeryman will create ManagedTask object when task is start.
::
  timer_task.apply_async((10,))


Usage
=====
Async task with ManagedTask and CeleryTask model.
::
  m = ManagedTask.objects.create(task_name='timer_task', celery_task_args=[10])
  m.set_task_args([10]) # if you don't use celery_task_args when created object, you can set with this method.
  m.start()
  m.stop()

Or use
::
  c = CeleryTask.objects.get(task_name='timer_task')
  c.set_task_args([10])
  managed_task = c.start()
  managed_task.stop()


Admin Panel
===========
To usable the async tasks:
http://localhost:8000/admin/celeryman/celerytask/

To view the created async tasks and to create new async task:
http://localhost:8000/admin/celeryman/managedtask/
