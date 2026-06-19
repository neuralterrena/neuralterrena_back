from django.conf import settings

from neuralterrena.customers.models import Client
from neuralterrena.customers.models import Domain


def test_django_tenants_is_configured() -> None:
    assert settings.DATABASES["default"]["ENGINE"] == "django_tenants.postgresql_backend"
    assert "django_tenants" in settings.SHARED_APPS
    assert settings.TENANT_MODEL == "customers.Client"
    assert settings.TENANT_DOMAIN_MODEL == "customers.Domain"
    assert settings.MIDDLEWARE[0] == "django_tenants.middleware.main.TenantMainMiddleware"


def test_customer_models_are_registered() -> None:
    assert Client._meta.app_label == "customers"
    assert Domain._meta.app_label == "customers"
