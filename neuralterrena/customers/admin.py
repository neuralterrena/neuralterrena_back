from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from unfold.admin import ModelAdmin

from .models import Client


@admin.register(Client)
class ClientAdmin(TenantAdminMixin, ModelAdmin):
    list_display = ("name", "schema_name", "created_on")
    search_fields = ("name", "schema_name")
    ordering = ("name",)
