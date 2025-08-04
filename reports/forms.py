from django import forms
from django.forms import formset_factory
from .models import TaskSubmission

class TaskSubmissionForm(forms.ModelForm):
    class Meta:
        model = TaskSubmission
        fields = ['task_type', 'description', 'equipment_type', 'shift', 'location', 'cause_of_problem', 'corrective_measure', 'start_time', 'end_time', 'team_members']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'placeholder': 'YYYY-MM-DD HH:MM', 'required': 'required'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'placeholder': 'YYYY-MM-DD HH:MM', 'required': 'required'}),
            'team_members': forms.SelectMultiple(attrs={'class': 'select2'}),
        }

TaskSubmissionFormSet = formset_factory(TaskSubmissionForm, extra=1, can_delete=True)