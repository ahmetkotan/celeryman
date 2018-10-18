from django.contrib import admin

# Register your models here.

from .models import CeleryTask, ManagedTask

class CeleryTaskAdmin(admin.ModelAdmin):
    list_display = ['task_name', 'last_run', 'is_active']
    list_filter = ['is_active']
    search_fields = ['task_name']
    ordering = ['-is_active', '-last_run']

    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.opts.local_fields]

    def has_delete_permission(self, request, obj=None):
        return False
    def has_add_permission(self, request):
        return False


    class Meta:
        model = CeleryTask


class ManagedTaskAdmin(admin.ModelAdmin):
    list_display = ['task_name', 'celery_task_id', 'celery_task_args', 'created_time', 'is_enable', 'celery_task_status', 'manual']
    list_filter = ['is_enable', 'task_name', 'celery_task_status', 'manual']
    ordering = ['-is_enable', 'celery_task_status', '-created_time']
    list_editable = ['is_enable']
    readonly_fields = ['task_name', 'celery_task_id', 'created_time', 'celery_task_status', 'manual']

    class Meta:
        model = ManagedTask


admin.site.register(CeleryTask, CeleryTaskAdmin)
admin.site.register(ManagedTask, ManagedTaskAdmin)