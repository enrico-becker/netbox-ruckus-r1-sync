from __future__ import annotations

import importlib
from django import forms
from netbox.forms import NetBoxModelForm

from .models import RuckusR1TenantConfig


def _resolve_dual_widget():
    """Return the NetBox dual-list widget class if available, else SelectMultiple.

    NetBox has changed widget locations/names across versions. We try a few known paths.
    """
    candidates = [
        # NetBox 4.x (varies by minor)
        ("utilities.forms.widgets.dual_listbox", "DualListbox"),
        ("utilities.forms.widgets.dual_select", "DualSelect"),
        ("utilities.forms.widgets", "DualListbox"),
        ("utilities.forms.widgets", "DualSelect"),
        # Older community forks
        ("utilities.forms.widgets", "DualListSelector"),
    ]
    for mod_name, cls_name in candidates:
        try:
            mod = importlib.import_module(mod_name)
            cls = getattr(mod, cls_name, None)
            if cls:
                return cls
        except Exception:
            continue
    return forms.SelectMultiple


_DualWidget = _resolve_dual_widget()


class RuckusR1TenantConfigForm(NetBoxModelForm):
    """Tenant config form with dual-list selector for venue selection.

    The model stores venue IDs in JSON field `venues_selected` (list[str]).
    The widget renders as two lists (available / selected) with move buttons when supported
    by the NetBox version. If not supported, it degrades to a normal multi-select.
    """

    venues_selected = forms.MultipleChoiceField(
        required=False,
        choices=(),
        widget=_DualWidget(),
        label="Venues to sync",
        help_text="If empty: sync ALL venues. Use the arrows to move venues between lists (if available).",
    )

    class Meta:
        model = RuckusR1TenantConfig
        fields = [
            # General
            "tenant",
            "name",
            "enabled",

            # API
            "api_base_url",
            "ruckus_tenant_id",
            "client_id",
            "client_secret",

            # Defaults
            "default_site_group",
            "default_device_role",
            "default_manufacturer",

            # Stubs
            "allow_stub_devices",
            "allow_stub_vlans",
            "allow_stub_wireless",

            # Sync toggles
            "sync_wlans",
            "sync_aps",
            "sync_switches",
            "sync_interfaces",
            "sync_wifi_clients",
            "sync_wired_clients",
            "sync_cabling",
            "sync_wireless_links",
            "sync_vlans",

            # Authoritative toggles
            "authoritative_devices",
            "authoritative_interfaces",
            "authoritative_ips",
            "authoritative_vlans",
            "authoritative_wireless",
            "authoritative_cabling",

            # Venue mapping
            "venue_mapping_mode",
            "venue_child_location_name",
            "venue_locations_parent_site",

            # Venue selection
            "venues_selected",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        inst = getattr(self, "instance", None)
        cache = list(getattr(inst, "venues_cache", []) or []) if inst and inst.pk else []
        selected = list(getattr(inst, "venues_selected", []) or []) if inst and inst.pk else []

        choices = []
        for v in cache:
            if not isinstance(v, dict):
                continue
            vid = (v.get("id") or "").strip()
            vname = (v.get("name") or vid).strip()
            if not vid:
                continue
            label = f"{vname} ({vid})" if vname and vname != vid else vid
            choices.append((vid, label))

        choices.sort(key=lambda x: (x[1].lower(), x[0]))
        self.fields["venues_selected"].choices = choices

        sel = set(selected)
        self.initial["venues_selected"] = [vid for vid, _ in choices if vid in sel]

    def clean_venues_selected(self):
        value = self.cleaned_data.get("venues_selected") or []
        return list(value)

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.venues_selected = self.cleaned_data.get("venues_selected") or []
        if commit:
            obj.save()
            self.save_m2m()
        return obj
