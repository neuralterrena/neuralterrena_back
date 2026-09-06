import pytest
from allauth.socialaccount.models import SocialLogin
from django.conf import settings

from neuralterrena.users.adapters import AccountAdapter
from neuralterrena.users.adapters import SocialAccountAdapter
from neuralterrena.users.models import User

pytestmark = pytest.mark.django_db


def test_social_account_adapter_is_open_for_signup(rf, settings):
    request = rf.get("/fake-url/")
    sociallogin = SocialLogin()
    adapter = SocialAccountAdapter()

    # Default is True
    assert adapter.is_open_for_signup(request, sociallogin) is True

    # Test with setting False
    settings.ACCOUNT_ALLOW_REGISTRATION = False
    assert adapter.is_open_for_signup(request, sociallogin) is False

    # Test with setting True
    settings.ACCOUNT_ALLOW_REGISTRATION = True
    assert adapter.is_open_for_signup(request, sociallogin) is True


def test_social_account_adapter_populate_user(rf):
    request = rf.get("/fake-url/")
    user_instance = User()
    sociallogin = SocialLogin(user=user_instance)
    adapter = SocialAccountAdapter()

    # Test case 1: name is provided directly
    data = {"name": "John Doe"}
    user = adapter.populate_user(request, sociallogin, data)
    assert user.name == "John Doe"

    # Test case 2: first_name and last_name are provided
    user_instance = User()
    sociallogin = SocialLogin(user=user_instance)
    data = {"first_name": "Jane", "last_name": "Smith"}
    user = adapter.populate_user(request, sociallogin, data)
    assert user.name == "Jane Smith"

    # Test case 3: only first_name is provided
    user_instance = User()
    sociallogin = SocialLogin(user=user_instance)
    data = {"first_name": "Bob"}
    user = adapter.populate_user(request, sociallogin, data)
    assert user.name == "Bob"

    # Test case 4: user already has a name
    user_instance = User(name="Existing Name")
    sociallogin = SocialLogin(user=user_instance)
    data = {"name": "New Name"}
    user = adapter.populate_user(request, sociallogin, data)
    assert user.name == "Existing Name"


def test_account_adapter_is_open_for_signup(rf, settings):
    request = rf.get("/fake-url/")
    adapter = AccountAdapter()

    # Default is True
    assert adapter.is_open_for_signup(request) is True

    # Test with setting False
    settings.ACCOUNT_ALLOW_REGISTRATION = False
    assert adapter.is_open_for_signup(request) is False

    # Test with setting True
    settings.ACCOUNT_ALLOW_REGISTRATION = True
    assert adapter.is_open_for_signup(request) is True
