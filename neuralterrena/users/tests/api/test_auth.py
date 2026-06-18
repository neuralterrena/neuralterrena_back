from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

from neuralterrena.users.tests.factories import UserFactory

if TYPE_CHECKING:
    from neuralterrena.users.models import User


@pytest.mark.django_db
class TestJWTAuthentication:
    password = "My_R@ndom-P@ssw0rd"  # noqa: S105

    @pytest.fixture
    def api_client(self) -> APIClient:
        return APIClient()

    def test_login_returns_access_and_refresh_cookie(self, api_client: APIClient):
        user = UserFactory.create(
            email="jwt@example.com",
            password=self.password,  # noqa: S106
        )

        response = api_client.post(
            "/api/auth/login/", data={"email": user.email, "password": self.password},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" not in response.data
        cookie = response.cookies[settings.JWT_AUTH_REFRESH_COOKIE]
        assert cookie.value
        assert cookie["httponly"]
        assert cookie["secure"]
        assert cookie["samesite"] == "Lax"
        assert cookie["path"] == "/api/auth/token/"

    def test_refresh_reads_cookie_and_rotates_token(self, api_client: APIClient):
        user = UserFactory.create(
            email="refresh@example.com",
            password=self.password,  # noqa: S106
        )
        login_response = api_client.post(
            "/api/auth/login/",
            data={"email": user.email, "password": self.password},
            format="json",
        )
        first_refresh = login_response.cookies[settings.JWT_AUTH_REFRESH_COOKIE].value

        refresh_response = api_client.post(
            "/api/auth/token/refresh/",
            data={},
            format="json",
        )

        assert refresh_response.status_code == status.HTTP_200_OK
        assert "access" in refresh_response.data
        assert "refresh" not in refresh_response.data
        rotated_refresh = refresh_response.cookies[
            settings.JWT_AUTH_REFRESH_COOKIE
        ].value
        assert rotated_refresh != first_refresh
        assert OutstandingToken.objects.filter(user=user).count() == len(
            {first_refresh, rotated_refresh},
        )
        assert BlacklistedToken.objects.count() == 1

    def test_refresh_requires_cookie(self, api_client: APIClient):
        response = api_client.post("/api/auth/token/refresh/", data={}, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["detail"] == "Refresh token cookie is missing."

    def test_jwt_authenticates_protected_endpoint(
        self,
        api_client: APIClient,
        user: User,
    ):
        user.set_password(self.password)
        user.save(update_fields=["password"])
        login_response = api_client.post(
            "/api/auth/login/",
            data={"email": user.email, "password": self.password},
            format="json",
        )
        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}",
        )

        response = api_client.get("/api/users/me/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == user.name


@pytest.mark.django_db
class TestPasswordResetAPI:
    @pytest.fixture
    def api_client(self) -> APIClient:
        return APIClient()

    def test_password_reset_request_sends_email(
        self,
        api_client: APIClient,
        mailoutbox,
    ):
        user = UserFactory.create(email="reset@example.com")

        response = api_client.post(
            "/api/auth/password-reset/",
            data={"email": user.email},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(mailoutbox) == 1
        assert user.email in mailoutbox[0].to
        assert "uid=" in mailoutbox[0].body
        assert "token=" in mailoutbox[0].body

    def test_password_reset_request_is_generic_for_unknown_email(
        self,
        api_client: APIClient,
        mailoutbox,
    ):
        response = api_client.post(
            "/api/auth/password-reset/",
            data={"email": "unknown@example.com"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert (
            response.data["detail"]
            == "If the account exists, a password reset email has been sent."
        )
        assert len(mailoutbox) == 0

    def test_password_reset_confirm_changes_password(self, api_client: APIClient):
        user = UserFactory.create(email="confirm@example.com")
        token_generator = PasswordResetTokenGenerator()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)

        response = api_client.post(
            "/api/auth/password-reset/confirm/",
            data={
                "uid": uid,
                "token": token,
                "new_password": "N3w-R@ndom-Passw0rd",
            },
            format="json",
        )

        user.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert user.check_password("N3w-R@ndom-Passw0rd")

    def test_password_reset_confirm_rejects_invalid_token(self, api_client: APIClient):
        user = UserFactory.create(email="badtoken@example.com")
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        response = api_client.post(
            "/api/auth/password-reset/confirm/",
            data={
                "uid": uid,
                "token": "invalid-token",
                "new_password": "N3w-R@ndom-Passw0rd",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["token"][0] == "Invalid or expired password reset token."
