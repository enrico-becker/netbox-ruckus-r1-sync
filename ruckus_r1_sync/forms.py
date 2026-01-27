from __future__ import annotations

from typing import List, Tuple

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


class DualListSelectorWidget(forms.SelectMultiple):
    """
    Two-list selector widget template (left=available, right=selected).
    Must inherit SelectMultiple so Django provides optgroups/choices in template context.
    """
    template_name = "ruckus_r1_sync/widgets/dual_list_selector.html"


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

    venues_selected = forms.MultipleChoiceField(
        label=_("Venues selected for Sync"),
        required=False,
        widget=DualListSelectorWidget(),
        help_text=_("Move Venues to the right to sync only those. Leave empty to sync ALL Venues."),
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

            # --- Mapping Roadmap ---
            "venue_mapping_mode",
            "venue_child_location_name",
            "venue_locations_parent_site",

            # --- Venue Roadmap ---
            "venues_selected",

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

    def _venue_choices_from_cache(self) -> List[Tuple[str, str]]:
        cache = getattr(self.instance, "venues_cache", None) or []
        out: List[Tuple[str, str]] = []
        for row in cache:
            if not isinstance(row, dict):
                continue
            vid = (row.get("id") or "").strip()
            name = (row.get("name") or vid or "").strip()
            if not vid:
                continue
            out.append((vid, name))
        out.sort(key=lambda x: (x[1] or "", x[0] or ""))
        return out

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        cur = getattr(self.instance, "api_base_url", None)
        if cur and cur not in dict(API_BASE_URL_CHOICES):
            self.fields["api_base_url"].choices = ((cur, cur),) + API_BASE_URL_CHOICES

        self.fields["venue_child_location_name"].help_text = _(
            "Used only when mapping mode is 'both' (Location name created under the Venue Site)."
        )

        # Choices from cached venues (Refresh Venues fills this)
        self.fields["venues_selected"].choices = self._venue_choices_from_cache()

        selected = getattr(self.instance, "venues_selected", None) or []
        if isinstance(selected, list):
            self.initial["venues_selected"] = [str(x) for x in selected]

    def clean(self):
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

        sel = cleaned.get("venues_selected") or []
        if not isinstance(sel, list):
            sel = list(sel)
        cleaned["venues_selected"] = [str(x).strip() for x in sel if str(x).strip()]

        return cleaned
