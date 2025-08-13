from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0005_inventory_models'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tasksubmission',
            name='time_taken',
            field=models.CharField(max_length=100, blank=True, null=True),
        ),
    ]