from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

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
    # New reporting fields
    date = models.DateField(default=timezone.now)
    shift = models.CharField(max_length=50, blank=True)
    reporter = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    equipment_type = models.CharField(max_length=100, blank=True)

    # Existing fields (renamed in UI as needed)
    task_type = models.CharField(max_length=2, choices=TASK_TYPES)
    description = models.TextField()  # Problem description
    cause_of_problem = models.TextField(blank=True)
    corrective_measure = models.TextField(blank=True)  # Corrective action

    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    time_taken = models.DurationField(null=True, blank=True)

    status = models.CharField(max_length=50, blank=True)
    remark = models.TextField(blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True)
    team_members = models.ManyToManyField(Engineer, related_name='tasks_assigned', blank=True)

    def save(self, *args, **kwargs):
        # Auto-compute time_taken if both times are present
        if self.start_time and self.end_time:
            calculated = self.end_time - self.start_time
            if calculated.total_seconds() >= 0:
                self.time_taken = calculated
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.task_type} by {self.engineer.name} on {self.date}"