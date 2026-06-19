from __future__ import annotations

from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenBlacklistSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

User = get_user_model()


class LoginSerializer(TokenObtainPairSerializer):
    username_field = User.USERNAME_FIELD


class CookieRefreshSerializer(serializers.Serializer):
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    default_error_messages = {
        "missing_refresh_cookie": _("Refresh token cookie is missing."),
    }

    def validate(self, attrs: dict[str, Any]) -> dict[str, str]:
        request = self.context["request"]
        refresh_cookie = request.COOKIES.get(settings.JWT_AUTH_REFRESH_COOKIE)
        if not refresh_cookie:
            raise exceptions.AuthenticationFailed(
                self.error_messages["missing_refresh_cookie"],
                code="missing_refresh_cookie",
            )

        serializer = TokenRefreshSerializer(data={"refresh": refresh_cookie})
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data


class LogoutSerializer(serializers.Serializer):
    default_error_messages = {
        "missing_refresh_cookie": _("Refresh token cookie is missing."),
    }

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        request = self.context["request"]
        refresh_cookie = request.COOKIES.get(settings.JWT_AUTH_REFRESH_COOKIE)
        if not refresh_cookie:
            raise exceptions.AuthenticationFailed(
                self.error_messages["missing_refresh_cookie"],
                code="missing_refresh_cookie",
            )

        serializer = TokenBlacklistSerializer(data={"refresh": refresh_cookie})
        serializer.is_valid(raise_exception=True)
        return {"refresh": refresh_cookie}


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    token_generator = PasswordResetTokenGenerator()

    def save(self) -> None:
        email = self.validated_data["email"].lower()
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if not user:
            return

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = self.token_generator.make_token(user)
        reset_url = self._build_reset_url(uid=uid, token=token)
        context = {
            "user": user,
            "reset_url": reset_url,
            "uid": uid,
            "token": token,
        }
        body = render_to_string(
            "account/email/password_reset_api_message.txt",
            context,
        )
        send_mail(
            subject="Password reset requested",
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )

    def _build_reset_url(self, *, uid: str, token: str) -> str:
        request = self.context["request"]
        frontend_url = settings.FRONTEND_RESET_PASSWORD_URL
        if frontend_url:
            return frontend_url.format(uid=uid, token=token)
        confirm_url = reverse("api:auth-password-reset-confirm")
        return request.build_absolute_uri(f"{confirm_url}?uid={uid}&token={token}")


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    default_error_messages = {
        "invalid_token": _("Invalid or expired password reset token."),
    }

    token_generator = PasswordResetTokenGenerator()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        user = self._get_user(attrs["uid"])
        token = attrs["token"]
        if not user or not self.token_generator.check_token(user, token):
            raise serializers.ValidationError(
                {"token": self.error_messages["invalid_token"]},
            )

        try:
            validate_password(attrs["new_password"], user)
        except exceptions.ValidationError as exc:
            raise serializers.ValidationError(
                {"new_password": list(exc.messages)},
            ) from exc
        attrs["user"] = user
        return attrs

    def save(self) -> None:
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])

    def _get_user(self, uid: str):
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            return User.objects.get(pk=user_id, is_active=True)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None
