from __future__ import annotations

from django import forms

from netbox.forms import NetBoxModelForm

from .models import RuckusR1TenantConfig


class RuckusR1TenantConfigForm(NetBoxModelForm):
    class Meta:
        model = RuckusR1TenantConfig
        fields = (
            "tenant",
            "name",
            "api_base_url",
            "ruckus_tenant_id",
            "client_id",
            "client_secret",
            "enabled",
            "allow_stub_devices",
            "allow_stub_vlans",
            "allow_stub_wireless",
            "authoritative_devices",
            "authoritative_interfaces",
            "authoritative_ips",
            "authoritative_vlans",
            "authoritative_wireless",
            "authoritative_cabling",
            "default_site_group",
            "default_device_role",
            "default_manufacturer",
        )
        help_texts = {
            "api_base_url": "z.B. https://api.eu.ruckus.cloud",
            "ruckus_tenant_id": "Tenant-ID für /oauth2/token/<tenantId>",
        }

    def clean_api_base_url(self):
        v = (self.cleaned_data.get("api_base_url") or "").strip()
        return v.rstrip("/")
 