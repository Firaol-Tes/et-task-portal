from django.db import models
from django.contrib.auth.models import User

class Engineer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    et_id = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    is_team_leader = models.BooleanField(default=False)  # Add this field

    def __str__(self):
        return f"{self.name} (ET-{self.et_id})"

class TaskSubmission(models.Model):
    TASK_TYPES = [
        ('PM', 'Preventive Maintenance'),
        ('RT', 'Routine Task'),
        ('MT', 'Maintenance Task'),
    ]
    engineer = models.ForeignKey(Engineer, on_delete=models.CASCADE)
    task_type = models.CharField(max_length=2, choices=TASK_TYPES)
    description = models.TextField()
    equipment_type = models.CharField(max_length=100, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    shift = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=100, blank=True)
    cause_of_problem = models.TextField(blank=True)
    corrective_measure = models.TextField(blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    team_members = models.ManyToManyField(Engineer, related_name='tasks_assigned', blank=True)

    def __str__(self):
        return f"{self.task_type} by {self.engineer.name}"