from django.db import migrations
from django.db import models
from django_tenants.postgresql_backend.base import _check_schema_name


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Client",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "schema_name",
                    models.CharField(
                        db_index=True,
                        max_length=63,
                        unique=True,
                        validators=[_check_schema_name],
                    ),
                ),
                ("name", models.CharField(max_length=255, unique=True, verbose_name="Tenant name")),
                ("created_on", models.DateTimeField(auto_now_add=True, verbose_name="Created on")),
            ],
            options={
                "verbose_name": "Client",
                "verbose_name_plural": "Clients",
                "ordering": ("name",),
            },
        ),
    ]
