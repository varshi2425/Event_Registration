import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create or update the deployment administrator from environment variables."

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_ADMIN_USERNAME")
        password = os.environ.get("DJANGO_ADMIN_PASSWORD")
        email = os.environ.get("DJANGO_ADMIN_EMAIL", "")

        if not username and not password:
            self.stdout.write("Deployment admin variables are not configured; skipping.")
            return

        if not username or not password:
            raise CommandError(
                "Set both DJANGO_ADMIN_USERNAME and DJANGO_ADMIN_PASSWORD."
            )

        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username=username,
            defaults={"email": email},
        )
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} deployment administrator."))
