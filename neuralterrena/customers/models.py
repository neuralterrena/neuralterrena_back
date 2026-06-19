from django.db import models
from django.utils.translation import gettext_lazy as _
from django_tenants.models import DomainMixin
from django_tenants.models import TenantMixin


class Client(TenantMixin):
    name = models.CharField(_("Tenant name"), max_length=255, unique=True)
    created_on = models.DateTimeField(_("Created on"), auto_now_add=True)

    auto_create_schema = True

    class Meta:
        verbose_name = _("Client")
        verbose_name_plural = _("Clients")
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Domain(DomainMixin):
    class Meta:
        verbose_name = _("Domain")
        verbose_name_plural = _("Domains")
        ordering = ("domain",)
