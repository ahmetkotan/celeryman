from django.core.exceptions import ValidationError

import json
import re

def task_name_validator(value):
    from celeryman.models import CeleryTask

    if type(value) == CeleryTask:
        return value.task_name
    else:
        task = CeleryTask.objects.filter(task_name=value)
        if task.exists():
            return task[0].task_name
        else:
            raise ValidationError("Invalid Task Name: %(task_name)s", params={'task_name': value})


def task_args_validator(value):
    list_patt = re.compile("\[(?P<elements>[\s\S]*)\]")

    if type(value) == str:
        if list_patt.match(value):
            elements = list_patt.search(value).group('elements')
            if elements:
                new_value = [i.strip() for i in elements.split(",")]
                new_value = [int(i) if i.isdigit() else i.replace("'", "").replace("\"", "") for i in new_value]
            else:
                new_value = []
        else:
            new_value = [i.strip() for i in value.split(",")]
            new_value = [int(i) if i.isdigit() else i.replace("'", "").replace("\"", "") for i in new_value]

        if new_value == []:
            return '[]'
        return json.dumps(new_value)
    elif type(value) == list or type(value) == tuple:
        if value == [] or value == ():
            return '[]'
        return json.dumps(value)

    return '[]'


