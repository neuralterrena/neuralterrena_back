from __future__ import annotations

import pytest
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.models import SocialLogin
from django.http import HttpRequest

from neuralterrena.users.adapters import AccountAdapter
from neuralterrena.users.adapters import SocialAccountAdapter
from neuralterrena.users.models import User

pytestmark = pytest.mark.django_db


class TestAccountAdapter:
    def test_is_open_for_signup_true(self, settings):
        settings.ACCOUNT_ALLOW_REGISTRATION = True
        adapter = AccountAdapter()
        request = HttpRequest()
        assert adapter.is_open_for_signup(request) is True

    def test_is_open_for_signup_false(self, settings):
        settings.ACCOUNT_ALLOW_REGISTRATION = False
        adapter = AccountAdapter()
        request = HttpRequest()
        assert adapter.is_open_for_signup(request) is False


class TestSocialAccountAdapter:
    def test_is_open_for_signup_true(self, settings):
        settings.ACCOUNT_ALLOW_REGISTRATION = True
        adapter = SocialAccountAdapter()
        request = HttpRequest()
        assert adapter.is_open_for_signup(request, None) is True

    def test_is_open_for_signup_false(self, settings):
        settings.ACCOUNT_ALLOW_REGISTRATION = False
        adapter = SocialAccountAdapter()
        request = HttpRequest()
        assert adapter.is_open_for_signup(request, None) is False

    def test_populate_user_with_name(self):
        adapter = SocialAccountAdapter()
        request = HttpRequest()
        sociallogin = SocialLogin(account=SocialAccount())
        user = User()
        sociallogin.user = user

        data = {"name": "John Doe"}
        populated_user = adapter.populate_user(request, sociallogin, data)
        assert populated_user.name == "John Doe"

    def test_populate_user_with_first_and_last_name(self):
        adapter = SocialAccountAdapter()
        request = HttpRequest()
        sociallogin = SocialLogin(account=SocialAccount())
        user = User()
        sociallogin.user = user

        data = {"first_name": "John", "last_name": "Doe"}
        populated_user = adapter.populate_user(request, sociallogin, data)
        assert populated_user.name == "John Doe"

    def test_populate_user_with_first_name_only(self):
        adapter = SocialAccountAdapter()
        request = HttpRequest()
        sociallogin = SocialLogin(account=SocialAccount())
        user = User()
        sociallogin.user = user

        data = {"first_name": "John"}
        populated_user = adapter.populate_user(request, sociallogin, data)
        assert populated_user.name == "John"
