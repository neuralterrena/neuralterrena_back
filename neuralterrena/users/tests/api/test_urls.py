from __future__ import annotations

from typing import TYPE_CHECKING

from django.urls import resolve
from django.urls import reverse

if TYPE_CHECKING:
    from neuralterrena.users.models import User


def test_user_detail(user: User):
    assert (
        reverse("api:user-detail", kwargs={"pk": user.pk}) == f"/api/users/{user.pk}/"
    )
    assert resolve(f"/api/users/{user.pk}/").view_name == "api:user-detail"


def test_user_list():
    assert reverse("api:user-list") == "/api/users/"
    assert resolve("/api/users/").view_name == "api:user-list"


def test_user_me():
    assert reverse("api:user-me") == "/api/users/me/"
    assert resolve("/api/users/me/").view_name == "api:user-me"


def test_auth_login():
    assert reverse("api:auth-login") == "/api/auth/login/"
    assert resolve("/api/auth/login/").view_name == "api:auth-login"


def test_auth_token_refresh():
    assert reverse("api:auth-token-refresh") == "/api/auth/token/refresh/"
    assert resolve("/api/auth/token/refresh/").view_name == "api:auth-token-refresh"


def test_auth_logout():
    assert reverse("api:auth-logout") == "/api/auth/token/logout/"
    assert resolve("/api/auth/token/logout/").view_name == "api:auth-logout"


def test_auth_password_reset():
    assert reverse("api:auth-password-reset") == "/api/auth/password-reset/"
    assert resolve("/api/auth/password-reset/").view_name == "api:auth-password-reset"


def test_auth_password_reset_confirm():
    assert (
        reverse("api:auth-password-reset-confirm")
        == "/api/auth/password-reset/confirm/"
    )
    assert (
        resolve("/api/auth/password-reset/confirm/").view_name
        == "api:auth-password-reset-confirm"
    )
