from django.conf import settings
from django.core.management.base import BaseCommand

from neuralterrena.customers.models import Client


class Command(BaseCommand):
    help = "Ensure the public tenant record exists."

    def handle(self, *args, **options):
        public_schema_name = settings.PUBLIC_SCHEMA_NAME
        public_tenant, created = Client.objects.get_or_create(
            schema_name=public_schema_name,
            defaults={"name": "Public"},
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created public tenant '{public_tenant.name}' "
                    f"for schema '{public_schema_name}'.",
                ),
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Public tenant already exists for schema '{public_schema_name}'.",
            ),
        )
