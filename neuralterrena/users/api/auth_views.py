from __future__ import annotations

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenViewBase

from .auth_serializers import CookieRefreshSerializer
from .auth_serializers import LoginSerializer
from .auth_serializers import PasswordResetConfirmSerializer
from .auth_serializers import PasswordResetRequestSerializer


class RefreshCookieMixin:
    def set_refresh_cookie(self, response: Response, refresh_token: str) -> None:
        response.set_cookie(
            key=settings.JWT_AUTH_REFRESH_COOKIE,
            value=refresh_token,
            httponly=settings.JWT_AUTH_REFRESH_COOKIE_HTTP_ONLY,
            secure=settings.JWT_AUTH_REFRESH_COOKIE_SECURE,
            samesite=settings.JWT_AUTH_REFRESH_COOKIE_SAMESITE,
            path=settings.JWT_AUTH_REFRESH_COOKIE_PATH,
            domain=settings.JWT_AUTH_REFRESH_COOKIE_DOMAIN,
        )


class LoginView(RefreshCookieMixin, TokenViewBase):
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        refresh_token = response.data.pop("refresh")
        self.set_refresh_cookie(response, refresh_token)
        return response


class RefreshTokenView(RefreshCookieMixin, TokenViewBase):
    permission_classes = (AllowAny,)
    serializer_class = CookieRefreshSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        refresh_token = response.data.pop("refresh", None)
        if refresh_token:
            self.set_refresh_cookie(response, refresh_token)
        return response


class PasswordResetRequestView(TokenViewBase):
    permission_classes = (AllowAny,)
    authentication_classes = ()
    serializer_class = PasswordResetRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "If the account exists, a password reset email has been sent."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(TokenViewBase):
    permission_classes = (AllowAny,)
    authentication_classes = ()
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Password has been reset successfully."},
            status=status.HTTP_200_OK,
        )
