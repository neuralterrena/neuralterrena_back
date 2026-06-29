from io import StringIO

import pytest
from django.core.management import call_command

from neuralterrena.customers.models import Client


@pytest.mark.django_db
def test_ensure_public_tenant_creates_missing_public_tenant():
    stdout = StringIO()

    call_command("ensure_public_tenant", stdout=stdout)

    public_tenant = Client.objects.get(schema_name="public")
    assert public_tenant.name == "Public"
    assert "Created public tenant" in stdout.getvalue()


@pytest.mark.django_db
def test_ensure_public_tenant_is_idempotent():
    Client.objects.create(name="Public API", schema_name="public")
    stdout = StringIO()

    call_command("ensure_public_tenant", stdout=stdout)

    assert Client.objects.filter(schema_name="public").count() == 1
    assert "already exists" in stdout.getvalue()
