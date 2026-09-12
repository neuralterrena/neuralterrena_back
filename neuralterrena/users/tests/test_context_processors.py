from django.test import RequestFactory

from neuralterrena.users.context_processors import allauth_settings


def test_allauth_settings(settings):
    """Test that allauth_settings context processor returns the correct setting."""
    settings.ACCOUNT_ALLOW_REGISTRATION = False

    rf = RequestFactory()
    request = rf.get("/")

    context = allauth_settings(request)
    assert context["ACCOUNT_ALLOW_REGISTRATION"] is False

    settings.ACCOUNT_ALLOW_REGISTRATION = True
    context = allauth_settings(request)
    assert context["ACCOUNT_ALLOW_REGISTRATION"] is True
