from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from unfold.admin import ModelAdmin

from .models import Client
from .models import Domain


@admin.register(Client)
class ClientAdmin(TenantAdminMixin, ModelAdmin):
    list_display = ("name", "schema_name", "created_on")
    search_fields = ("name", "schema_name")
    ordering = ("name",)


@admin.register(Domain)
class DomainAdmin(ModelAdmin):
    list_display = ("domain", "tenant", "is_primary")
    list_filter = ("is_primary",)
    search_fields = ("domain", "tenant__name", "tenant__schema_name")
    ordering = ("domain",)
