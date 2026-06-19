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
from rest_framework_simplejwt.tokens import UntypedToken

from neuralterrena.customers.models import Client
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
        client = Client.objects.create(name="Acme", schema_name="acme")
        user = UserFactory.create(
            email="jwt@example.com",
            name="Jane Doe",
            password=self.password,
            client=client,
        )

        response = api_client.post(
            "/api/auth/login/",
            data={"email": user.email, "password": self.password},
            format="json",
            HTTP_X_CLIENT_ID=str(client.id),
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
        payload = UntypedToken(response.data["access"]).payload
        assert payload["name"] == user.name
        assert payload["email"] == user.email
        assert payload["client_id"] == client.id
        assert payload["client__name"] == client.name

    def test_refresh_reads_cookie_and_rotates_token(self, api_client: APIClient):
        client = Client.objects.create(name="Refresh", schema_name="refresh")
        user = UserFactory.create(
            email="refresh@example.com",
            password=self.password,
            client=client,
        )
        login_response = api_client.post(
            "/api/auth/login/",
            data={"email": user.email, "password": self.password},
            format="json",
            HTTP_X_CLIENT_ID=str(client.id),
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

    def test_logout_blacklists_refresh_and_clears_cookie(self, api_client: APIClient):
        client = Client.objects.create(name="Logout", schema_name="logout")
        user = UserFactory.create(
            email="logout@example.com",
            password=self.password,
            client=client,
        )
        login_response = api_client.post(
            "/api/auth/login/",
            data={"email": user.email, "password": self.password},
            format="json",
            HTTP_X_CLIENT_ID=str(client.id),
        )
        refresh_token = login_response.cookies[settings.JWT_AUTH_REFRESH_COOKIE].value

        logout_response = api_client.post(
            "/api/auth/token/logout/",
            data={},
            format="json",
        )

        assert logout_response.status_code == status.HTTP_200_OK
        assert logout_response.data["detail"] == "Logout completed successfully."
        assert BlacklistedToken.objects.count() == 1
        cleared_cookie = logout_response.cookies[settings.JWT_AUTH_REFRESH_COOKIE]
        assert cleared_cookie.value == ""
        assert cleared_cookie["max-age"] == 0

        refresh_response = api_client.post(
            "/api/auth/token/refresh/",
            data={},
            format="json",
        )
        assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED
        assert str(BlacklistedToken.objects.first().token.token) == refresh_token

    def test_jwt_authenticates_protected_endpoint(
        self,
        api_client: APIClient,
        user: User,
    ):
        client = Client.objects.create(name="Users", schema_name="users")
        user.client = client
        user.set_password(self.password)
        user.save(update_fields=["client", "password"])
        login_response = api_client.post(
            "/api/auth/login/",
            data={"email": user.email, "password": self.password},
            format="json",
            HTTP_X_CLIENT_ID=str(client.id),
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
        client = Client.objects.create(name="Reset", schema_name="reset")
        user = UserFactory.create(email="reset@example.com", client=client)

        response = api_client.post(
            "/api/auth/password-reset/",
            data={"email": user.email},
            format="json",
            HTTP_X_CLIENT_ID=str(client.id),
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
        client = Client.objects.create(name="Unknown", schema_name="unknown")
        response = api_client.post(
            "/api/auth/password-reset/",
            data={"email": "unknown@example.com"},
            format="json",
            HTTP_X_CLIENT_ID=str(client.id),
        )

        assert response.status_code == status.HTTP_200_OK
        assert (
            response.data["detail"]
            == "If the account exists, a password reset email has been sent."
        )
        assert len(mailoutbox) == 0

    def test_password_reset_confirm_changes_password(self, api_client: APIClient):
        client = Client.objects.create(name="Confirm", schema_name="confirm")
        user = UserFactory.create(email="confirm@example.com", client=client)
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
            HTTP_X_CLIENT_ID=str(client.id),
        )

        user.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert user.check_password("N3w-R@ndom-Passw0rd")

    def test_password_reset_confirm_rejects_invalid_token(self, api_client: APIClient):
        client = Client.objects.create(name="Bad Token", schema_name="badtoken")
        user = UserFactory.create(email="badtoken@example.com", client=client)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        response = api_client.post(
            "/api/auth/password-reset/confirm/",
            data={
                "uid": uid,
                "token": "invalid-token",
                "new_password": "N3w-R@ndom-Passw0rd",
            },
            format="json",
            HTTP_X_CLIENT_ID=str(client.id),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["token"][0] == "Invalid or expired password reset token."
