from allauth.account.adapter import get_adapter
from django.conf import settings

from neuralterrena.users.context_processors import allauth_settings


def test_signup_is_closed(rf):
    request = rf.get("/accounts/signup/")

    assert not get_adapter(request).is_open_for_signup(request)

def test_templates_receive_signup_disabled_flag(rf):
    request = rf.get("/accounts/login/")

    assert allauth_settings(request)["ACCOUNT_ALLOW_REGISTRATION"] is False

def test_password_reset_timeout_is_one_day():
    assert settings.PASSWORD_RESET_TIMEOUT == 60 * 60 * 24


def test_social_login_app_is_disabled():
    assert "allauth.socialaccount" not in settings.INSTALLED_APPS
