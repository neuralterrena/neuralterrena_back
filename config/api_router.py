from django.conf import settings
from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter

from neuralterrena.users.api.auth_views import LoginView
from neuralterrena.users.api.auth_views import LogoutView
from neuralterrena.users.api.auth_views import PasswordResetConfirmView
from neuralterrena.users.api.auth_views import PasswordResetRequestView
from neuralterrena.users.api.auth_views import RefreshTokenView
from neuralterrena.users.api.views import UserViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

router.register("users", UserViewSet)


app_name = "api"
urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/token/refresh/", RefreshTokenView.as_view(), name="auth-token-refresh"),
    path("auth/token/logout/", LogoutView.as_view(), name="auth-logout"),
    path(
        "auth/password-reset/",
        PasswordResetRequestView.as_view(),
        name="auth-password-reset",
    ),
    path(
        "auth/password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="auth-password-reset-confirm",
    ),
    *router.urls,
]
