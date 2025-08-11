from django import forms
from django.forms import formset_factory
from .models import TaskSubmission

class TaskSubmissionForm(forms.ModelForm):
    class Meta:
        model = TaskSubmission
        fields = [
            'date', 'shift', 'reporter', 'location', 'equipment_type',
            'task_type', 'description', 'cause_of_problem', 'corrective_measure',
            'start_time', 'end_time', 'time_taken', 'status', 'remark', 'team_members'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'required': 'required'}),
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'placeholder': 'YYYY-MM-DD HH:MM'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'placeholder': 'YYYY-MM-DD HH:MM'}),
            'team_members': forms.SelectMultiple(attrs={'class': 'select2'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'cause_of_problem': forms.Textarea(attrs={'rows': 2}),
            'corrective_measure': forms.Textarea(attrs={'rows': 2}),
            'remark': forms.Textarea(attrs={'rows': 2}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_time')
        end = cleaned.get('end_time')
        if start and end and end < start:
            self.add_error('end_time', 'End time must be after start time')
        return cleaned

TaskSubmissionFormSet = formset_factory(TaskSubmissionForm, extra=0, can_delete=False)