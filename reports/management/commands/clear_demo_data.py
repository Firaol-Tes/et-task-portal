from django.core.management.base import BaseCommand
from django.db import transaction
import os

class Command(BaseCommand):
    help = "Clear demo data (TaskSubmission, InventoryItem, InventoryTransaction) when CLEAR_DEMO_DATA=true."

    def handle(self, *args, **options):
        flag = os.getenv("CLEAR_DEMO_DATA", "").strip().lower()
        if flag not in {"1", "true", "yes"}:
            self.stdout.write("clear_demo_data: flag not set; skipping")
            return

        from reports.models import TaskSubmission, InventoryItem, InventoryTransaction

        with transaction.atomic():
            tasks_deleted, _ = TaskSubmission.objects.all().delete()
            tx_deleted, _ = InventoryTransaction.objects.all().delete()
            items_deleted, _ = InventoryItem.objects.all().delete()

        self.stdout.write(
            f"clear_demo_data: deleted tasks={tasks_deleted}, transactions={tx_deleted}, items={items_deleted}"
        )