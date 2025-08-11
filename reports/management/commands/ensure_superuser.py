from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os


class Command(BaseCommand):
    help = "Ensure a superuser exists using DJANGO_SUPERUSER_USERNAME/EMAIL/PASSWORD env vars."

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.getenv("DJANGO_SUPERUSER_USERNAME")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD")

        if not username or not password:
            self.stdout.write(
                "ensure_superuser: DJANGO_SUPERUSER_USERNAME or DJANGO_SUPERUSER_PASSWORD not set; skipping"
            )
            return

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email}
        )

        changed = False
        if not user.is_staff or not user.is_superuser:
            user.is_staff = True
            user.is_superuser = True
            changed = True

        # Always set password from env to ensure you know it
        user.set_password(password)
        changed = True

        if changed or created:
            user.save()

        self.stdout.write(
            f"ensure_superuser: ensured superuser '{username}' (created={created})"
        )