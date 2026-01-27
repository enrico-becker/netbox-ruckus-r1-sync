from __future__ import annotations

from django import forms
from django.utils.translation import gettext_lazy as _

from netbox.forms import NetBoxModelForm
from .models import RuckusR1TenantConfig


API_BASE_URL_CHOICES = (
    ("https://api.asia.ruckus.cloud", _("Asia – https://api.asia.ruckus.cloud")),
    ("https://api.eu.ruckus.cloud", _("Europe – https://api.eu.ruckus.cloud")),
    ("https://api.ruckus.cloud", _("North America – https://api.ruckus.cloud")),
)


class RuckusR1TenantConfigForm(NetBoxModelForm):
    api_base_url = forms.ChoiceField(
        label=_("API base URL / Region"),
        choices=API_BASE_URL_CHOICES,
        required=True,
    )

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



            # authoritativeness + stubs
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ensure current value is selectable (e.g. old configs)
        cur = getattr(self.instance, "api_base_url", None)
        if cur and cur not in dict(API_BASE_URL_CHOICES):
            self.fields["api_base_url"].choices = ((cur, cur),) + API_BASE_URL_CHOICES
