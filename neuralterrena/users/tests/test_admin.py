import contextlib
from http import HTTPStatus
from importlib import reload

import pytest
from allauth.account.models import EmailAddress
from django.contrib import admin
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from neuralterrena.users.models import User


class TestUserAdmin:
    def test_index_uses_unfold_branding(self, admin_client):
        response = admin_client.get(reverse("admin:index"))

        assert response.status_code == HTTPStatus.OK
        assert b"Neural Terrena Console" in response.content
        assert b"/static/unfold/css/styles.css" in response.content
        assert b"unfold-neuralterrena.css" in response.content
        assert b"NT-logo-color-horizontal.png" in response.content

    def test_changelist(self, admin_client):
        url = reverse("admin:users_user_changelist")
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_search(self, admin_client):
        url = reverse("admin:users_user_changelist")
        response = admin_client.get(url, data={"q": "test"})
        assert response.status_code == HTTPStatus.OK

    def test_add(self, admin_client):
        url = reverse("admin:users_user_add")
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

        response = admin_client.post(
            url,
            data={
                "email": "new-admin@example.com",
                "name": "New Admin",
            },
        )
        assert response.status_code == HTTPStatus.FOUND
        user = User.objects.get(email="new-admin@example.com")
        assert user.name == "New Admin"
        assert not user.has_usable_password()

        email_address = EmailAddress.objects.get(user=user, email=user.email)
        assert email_address.primary
        assert email_address.verified

    def test_add_sends_password_setup_email(self, admin_client, mailoutbox):
        url = reverse("admin:users_user_add")
        response = admin_client.post(
            url,
            data={
                "email": "invited-user@example.com",
                "name": "Invited User",
            },
        )

        assert response.status_code == HTTPStatus.FOUND
        assert len(mailoutbox) == 1
        assert mailoutbox[0].to == ["invited-user@example.com"]
        assert "/accounts/password/reset/key/" in mailoutbox[0].body

    def test_resend_password_setup_email_action(self, admin_client, mailoutbox):
        user = User.objects.create_user(email="resend@example.com")
        url = reverse("admin:users_user_changelist")
        response = admin_client.post(
            url,
            data={
                "action": "resend_password_setup_email",
                "_selected_action": [str(user.pk)],
            },
        )

        assert response.status_code == HTTPStatus.FOUND
        assert len(mailoutbox) == 1
        assert mailoutbox[0].to == ["resend@example.com"]
        assert EmailAddress.objects.get(user=user, email="resend@example.com").verified

    def test_view_user(self, admin_client):
        user = User.objects.get(email="admin@example.com")
        url = reverse("admin:users_user_change", kwargs={"object_id": user.pk})
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

    @pytest.fixture
    def _force_allauth(self, settings):
        settings.DJANGO_ADMIN_FORCE_ALLAUTH = True
        # Reload the admin module to apply the setting change
        import neuralterrena.users.admin as users_admin  # noqa: PLC0415

        with contextlib.suppress(admin.sites.AlreadyRegistered):  # type: ignore[attr-defined]
            reload(users_admin)

    @pytest.mark.django_db
    @pytest.mark.usefixtures("_force_allauth")
    def test_allauth_login(self, rf, settings):
        request = rf.get("/fake-url")
        request.user = AnonymousUser()
        response = admin.site.login(request)

        # The `admin` login view should redirect to the `allauth` login view
        target_url = reverse(settings.LOGIN_URL) + "?next=" + request.path
        assertRedirects(response, target_url, fetch_redirect_response=False)
