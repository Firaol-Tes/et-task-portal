from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Engineer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    et_id = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    is_team_leader = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} (ET-{self.et_id})"

class TaskSubmission(models.Model):
    TASK_TYPES = [
        ('PM', 'Preventive Maintenance'),
        ('RT', 'Routine Task'),
        ('MT', 'Maintenance Task'),
    ]

    engineer = models.ForeignKey(Engineer, on_delete=models.CASCADE)

    # Reporting fields
    date = models.DateField(default=timezone.now)
    shift = models.CharField(max_length=50, blank=True)
    reporter = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    equipment_type = models.CharField(max_length=100, blank=True)

    # Task details
    task_type = models.CharField(max_length=2, choices=TASK_TYPES)
    description = models.TextField()  # Problem description
    cause_of_problem = models.TextField(blank=True)
    corrective_measure = models.TextField(blank=True)  # Corrective action

    # Timing
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    time_taken = models.CharField(max_length=100, blank=True, null=True)

    # Status/remarks
    status = models.CharField(max_length=50, blank=True)
    remark = models.TextField(blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True)
    team_members = models.ManyToManyField(Engineer, related_name='tasks_assigned', blank=True)

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            calculated = self.end_time - self.start_time
            if calculated.total_seconds() >= 0 and not self.time_taken:
                self.time_taken = str(calculated)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.task_type} by {self.engineer.name} on {self.date}"

class InventoryItem(models.Model):
    number = models.AutoField(primary_key=True)
    item = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    @property
    def balance(self):
        return self.quantity * self.price

    def decrease(self, amount: int):
        if amount < 0:
            raise ValueError("Amount must be non-negative")
        if amount > self.quantity:
            amount = self.quantity
        self.quantity -= amount
        self.save(update_fields=["quantity"])

    def __str__(self) -> str:
        return f"{self.number}. {self.item}"

class InventoryTransaction(models.Model):
    ACTION_CHOICES = (
        ("TAKE", "Take"),
        ("ADD", "Add"),
    )
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name="transactions")
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    quantity = models.PositiveIntegerField()
    at = models.DateTimeField(auto_now_add=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def apply(self):
        if self.action == "TAKE":
            self.item.decrease(self.quantity)
        elif self.action == "ADD":
            self.item.quantity += self.quantity
            self.item.save(update_fields=["quantity"])