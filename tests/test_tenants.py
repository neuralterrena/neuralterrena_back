from django.conf import settings

from neuralterrena.customers.models import Client


def test_django_tenants_is_configured() -> None:
    assert (
        settings.DATABASES["default"]["ENGINE"]
        == "django_tenants.postgresql_backend"
    )
    assert "django_tenants" in settings.SHARED_APPS
    assert settings.TENANT_MODEL == "customers.Client"
    assert (
        settings.MIDDLEWARE[0]
        == "neuralterrena.customers.middleware.JWTTenantMiddleware"
    )


def test_customer_models_are_registered() -> None:
    assert Client.__module__ == "neuralterrena.customers.models"
