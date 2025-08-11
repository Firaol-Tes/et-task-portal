from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0003_engineer_is_team_leader_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='tasksubmission',
            name='date',
            field=models.DateField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='tasksubmission',
            name='reporter',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='tasksubmission',
            name='status',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='tasksubmission',
            name='remark',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='tasksubmission',
            name='time_taken',
            field=models.DurationField(blank=True, null=True),
        ),
    ]