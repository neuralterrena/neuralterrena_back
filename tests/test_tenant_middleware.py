from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock

from django.db import ProgrammingError
from rest_framework_simplejwt.tokens import AccessToken

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
        client_manager_mock.filter.return_value.first.return_value = client

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
        client_manager_mock.filter.return_value.first.return_value = client

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

    def test_skips_tenant_binding_when_customers_table_is_unavailable(
        self,
        monkeypatch,
        rf: RequestFactory,
    ):
        response = object()
        get_response = Mock(return_value=response)
        connection_mock = Mock()
        middleware = JWTTenantMiddleware(get_response)
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

        assert middleware(request) is response
        assert request.tenant is None
        connection_mock.set_tenant.assert_not_called()
        connection_mock.set_schema_to_public.assert_not_called()
