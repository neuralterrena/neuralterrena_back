from __future__ import annotations

import json
import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import OperationalError
from django.db import ProgrammingError
from django.db import connection
from django.http import Http404
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import UntypedToken

from neuralterrena.customers.models import Client

logger = logging.getLogger(__name__)


class TenantTableUnavailableError(Exception):
    """Raised when the shared tenant table has not been created yet."""


TENANT_TABLE_UNAVAILABLE_MESSAGE = (
    "Tenant resolution is unavailable because the shared customers table is missing. "
    "Run `uv run python manage.py migrate_schemas --shared` and create the public tenant."
)


class JWTTenantMiddleware:
    """
    Resolve the active tenant from the JWT `client_id` claim.

    Unauthenticated endpoints can provide the tenant through the refresh cookie
    or the `X-Client-Id` header.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_authentication = JWTAuthentication()

    def __call__(self, request):
        try:
            tenant = self.get_tenant(request)
        except TenantTableUnavailableError:
            raise ImproperlyConfigured(TENANT_TABLE_UNAVAILABLE_MESSAGE) from None

        request.tenant = tenant

        if tenant is None:
            return self.get_response(request)

        connection.set_tenant(tenant)

        try:
            return self.get_response(request)
        finally:
            connection.set_schema_to_public()

    def get_tenant(self, request) -> Client | None:
        tenant = self.get_tenant_from_jwt(request)
        if tenant is not None:
            return tenant

        tenant = self.get_tenant_from_refresh_cookie(request)
        if tenant is not None:
            return tenant

        tenant = self.get_tenant_from_request_client_id(request)
        if tenant is not None:
            return tenant

        tenant = self.get_public_tenant()
        if tenant is not None:
            return tenant

        msg = "No tenant could be resolved for this request."
        raise Http404(msg)

    def get_tenant_from_jwt(self, request) -> Client | None:
        header = self.jwt_authentication.get_header(request)
        if header is None:
            return None

        raw_token = self.jwt_authentication.get_raw_token(header)
        if raw_token is None:
            return None

        try:
            validated_token = self.jwt_authentication.get_validated_token(raw_token)
        except (InvalidToken, TokenError):
            return None

        client_id = validated_token.get("client_id")
        return self.get_client(client_id)

    def get_tenant_from_refresh_cookie(self, request) -> Client | None:
        refresh_cookie = request.COOKIES.get(settings.JWT_AUTH_REFRESH_COOKIE)
        if not refresh_cookie:
            return None

        try:
            validated_token = UntypedToken(refresh_cookie)
        except (InvalidToken, TokenError):
            return None

        client_id = validated_token.get("client_id")
        return self.get_client(client_id)

    def get_tenant_from_request_client_id(self, request) -> Client | None:
        client_id = request.headers.get("X-Client-Id")
        if client_id is None:
            client_id = request.GET.get("client_id")
        if client_id is None:
            client_id = self.get_client_id_from_body(request)

        return self.get_client(client_id)

    def get_client_id_from_body(self, request) -> int | str | None:
        if request.method not in {"POST", "PUT", "PATCH"}:
            return None

        content_type = request.content_type or ""
        if "application/json" in content_type:
            try:
                payload = json.loads(request.body.decode("utf-8") or "{}")
            except (json.JSONDecodeError, UnicodeDecodeError):
                return None
            return payload.get("client_id")

        return request.POST.get("client_id")

    def get_client(self, client_id) -> Client | None:
        if client_id is None:
            return None

        return self._safe_lookup(pk=client_id)

    def get_public_tenant(self) -> Client | None:
        return self._safe_lookup(schema_name=settings.PUBLIC_SCHEMA_NAME)

    def _safe_lookup(self, **filters) -> Client | None:
        try:
            return Client.objects.filter(**filters).first()
        except (OperationalError, ProgrammingError):
            logger.warning(
                "Tenant lookup skipped because the customers table is unavailable.",
                exc_info=True,
            )
            raise TenantTableUnavailableError from None
