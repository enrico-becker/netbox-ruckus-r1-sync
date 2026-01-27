from __future__ import annotations

from django import forms
from django.utils.translation import gettext_lazy as _

from dcim.models import Site
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

    venue_locations_parent_site = forms.ModelChoiceField(
        label=_("Parent Site (required for 'locations' mode)"),
        queryset=Site.objects.all().order_by("name"),
        required=False,
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

            # --- Mapping Roadmap (neu) ---
            "venue_mapping_mode",
            "venue_child_location_name",
            "venue_locations_parent_site",

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

        # UX: help text
        self.fields["venue_child_location_name"].help_text = _(
            "Used only when mapping mode is 'both' (Location name created under the Venue Site)."
        )

    def clean(self):
        # NetBox may return None here; in that case we MUST preserve existing cleaned_data
        cleaned = super().clean()
        if cleaned is None:
            cleaned = self.cleaned_data

        mode = (cleaned.get("venue_mapping_mode") or "").strip().lower()
        parent_site = cleaned.get("venue_locations_parent_site")
        child_name = (cleaned.get("venue_child_location_name") or "").strip()

        if mode == RuckusR1TenantConfig.VENUE_MAPPING_LOCATIONS and not parent_site:
            self.add_error(
                "venue_locations_parent_site",
                _("This field is required when mapping mode is 'locations'."),
            )

        if mode == RuckusR1TenantConfig.VENUE_MAPPING_BOTH:
            cleaned["venue_child_location_name"] = child_name or "Venue"

        return cleaned
