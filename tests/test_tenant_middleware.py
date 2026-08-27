from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.db import ProgrammingError
from django.http import Http404
from rest_framework_simplejwt.tokens import AccessToken

from neuralterrena.customers.middleware import TENANT_TABLE_UNAVAILABLE_MESSAGE
from neuralterrena.customers.middleware import JWTTenantMiddleware
from neuralterrena.customers.models import Client

if TYPE_CHECKING:
    from django.test import RequestFactory


class TestJWTTenantMiddleware:
    def test_uses_client_id_from_jwt(self, monkeypatch, rf: RequestFactory):
        client = Client(name="Acme", schema_name="acme")
        client.pk = 7
        token = AccessToken()
        token["client_id"] = client.pk
        connection_mock = Mock()
        middleware = JWTTenantMiddleware(lambda request: request)
        client_manager_mock = Mock()
        mock_first = client_manager_mock.filter.return_value.order_by.return_value.first
        mock_first.return_value = client

        monkeypatch.setattr(
            "neuralterrena.customers.middleware.connection",
            connection_mock,
        )
        monkeypatch.setattr(
            "neuralterrena.customers.middleware.Client.objects",
            client_manager_mock,
        )

        request = rf.get("/api/users/me/", HTTP_AUTHORIZATION=f"Bearer {token}")

        response = middleware(request)

        assert response.tenant == client
        client_manager_mock.filter.assert_called_once_with(pk=client.pk)
        connection_mock.set_tenant.assert_called_once_with(client)
        connection_mock.set_schema_to_public.assert_called_once_with()

    def test_uses_client_id_from_header_when_jwt_is_missing(
        self,
        monkeypatch,
        rf: RequestFactory,
    ):
        client = Client(name="Globex", schema_name="globex")
        connection_mock = Mock()
        middleware = JWTTenantMiddleware(lambda request: request)
        client_manager_mock = Mock()
        mock_first = client_manager_mock.filter.return_value.order_by.return_value.first
        mock_first.return_value = client

        monkeypatch.setattr(
            "neuralterrena.customers.middleware.connection",
            connection_mock,
        )
        monkeypatch.setattr(
            "neuralterrena.customers.middleware.Client.objects",
            client_manager_mock,
        )

        request = rf.post("/api/auth/login/", HTTP_X_CLIENT_ID="13")

        response = middleware(request)

        assert response.tenant == client
        client_manager_mock.filter.assert_called_once_with(pk="13")
        connection_mock.set_tenant.assert_called_once_with(client)
        connection_mock.set_schema_to_public.assert_called_once_with()

    def test_raises_clear_error_when_customers_table_is_unavailable(
        self,
        monkeypatch,
        rf: RequestFactory,
    ):
        connection_mock = Mock()
        middleware = JWTTenantMiddleware(lambda request: request)
        client_manager_mock = Mock()
        client_manager_mock.filter.side_effect = ProgrammingError(
            'relation "customers_client" does not exist',
        )

        monkeypatch.setattr(
            "neuralterrena.customers.middleware.connection",
            connection_mock,
        )
        monkeypatch.setattr(
            "neuralterrena.customers.middleware.Client.objects",
            client_manager_mock,
        )

        request = rf.get("/api/docs/")

        with pytest.raises(ImproperlyConfigured, match="shared customers table"):
            middleware(request)

        connection_mock.set_tenant.assert_not_called()
        connection_mock.set_schema_to_public.assert_not_called()

    def test_tenant_table_error_message_guides_recovery(self):
        assert "migrate_schemas --shared" in TENANT_TABLE_UNAVAILABLE_MESSAGE
        assert "public tenant" in TENANT_TABLE_UNAVAILABLE_MESSAGE

    def test_keeps_rejecting_non_admin_requests_without_public_tenant(
        self,
        monkeypatch,
        rf: RequestFactory,
    ):
        middleware = JWTTenantMiddleware(lambda request: request)
        client_manager_mock = Mock()
        mock_first = client_manager_mock.filter.return_value.order_by.return_value.first
        mock_first.return_value = None

        monkeypatch.setattr(
            "neuralterrena.customers.middleware.Client.objects",
            client_manager_mock,
        )

        request = rf.get("/api/docs/")

        with pytest.raises(Http404, match="No tenant could be resolved"):
            middleware(request)
