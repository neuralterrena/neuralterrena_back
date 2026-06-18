from __future__ import annotations

from typing import TYPE_CHECKING

from allauth.account.forms import default_token_generator
from allauth.account.internal import flows
from allauth.account.models import EmailAddress
from allauth.core.context import request_context
from django.db import transaction

if TYPE_CHECKING:
    from django.contrib.auth.base_user import AbstractBaseUser
    from django.http import HttpRequest


def send_password_setup_email(request: HttpRequest, user: AbstractBaseUser) -> None:
    _ensure_verified_email(user)
    with request_context(request):
        flows.password_reset.request_password_reset(
            request,
            user.email,
            [user],
            default_token_generator,
        )


@transaction.atomic
def _ensure_verified_email(user: AbstractBaseUser) -> None:
    email = user.email.lower()
    if user.email != email:
        user.email = email
        user.save(update_fields=["email"])

    EmailAddress.objects.filter(user=user).exclude(email=email).update(primary=False)
    email_address, _ = EmailAddress.objects.update_or_create(
        user=user,
        email=email,
        defaults={
            "primary": True,
            "verified": True,
        },
    )
    if not email_address.primary or not email_address.verified:
        email_address.primary = True
        email_address.verified = True
        email_address.save(update_fields=["primary", "verified"])
