from __future__ import annotations

from django.db import models
from django.urls import reverse
from dcim.models import Site

from netbox.models import NetBoxModel
from tenancy.models import Tenant


class RuckusR1TenantConfig(NetBoxModel):
    # --- Venue mapping (neu) ---
    VENUE_MAPPING_SITES = "sites"
    VENUE_MAPPING_LOCATIONS = "locations"
    VENUE_MAPPING_BOTH = "both"

    VENUE_MAPPING_CHOICES = (
        (VENUE_MAPPING_SITES, "Sites (Venue → Site)"),
        (VENUE_MAPPING_LOCATIONS, "Locations (Venue → Location under Parent Site)"),
        (VENUE_MAPPING_BOTH, "Both (Venue → Site + child Location)"),
    )

    tenant = models.OneToOneField(
        to=Tenant,
        on_delete=models.CASCADE,
        related_name="ruckus_r1_sync_config",
        unique=True,
    )

    name = models.CharField(max_length=200)

    api_base_url = models.CharField(
        max_length=200,
        default="https://api.eu.ruckus.cloud",
        help_text="RUCKUS Cloud API base URL (example: https://api.eu.ruckus.cloud)",
    )

    ruckus_tenant_id = models.CharField(
        max_length=128,
        help_text="RUCKUS Cloud tenantId used for token endpoint /oauth2/token/<tenantId>",
    )

    client_id = models.CharField(max_length=256)
    client_secret = models.CharField(max_length=256)

    enabled = models.BooleanField(default=True)

    allow_stub_devices = models.BooleanField(default=True)
    allow_stub_vlans = models.BooleanField(default=True)
    allow_stub_wireless = models.BooleanField(default=True)
    sync_wlans = models.BooleanField(default=True)
    sync_aps = models.BooleanField(default=True)
    sync_switches = models.BooleanField(default=True)
    sync_interfaces = models.BooleanField(default=True)
    sync_wifi_clients = models.BooleanField(default=True)
    sync_wired_clients = models.BooleanField(default=True)
    sync_cabling = models.BooleanField(default=True)
    sync_wireless_links = models.BooleanField(default=True)
    sync_vlans = models.BooleanField(default=False)  # wenn du VLAN später implementierst
    authoritative_devices = models.BooleanField(default=False)
    authoritative_interfaces = models.BooleanField(default=False)
    authoritative_ips = models.BooleanField(default=False)
    authoritative_vlans = models.BooleanField(default=False)
    authoritative_wireless = models.BooleanField(default=False)
    authoritative_cabling = models.BooleanField(default=False)

    default_site_group = models.CharField(max_length=200, default="", blank=True)
    default_device_role = models.CharField(max_length=200, default="", blank=True)
    default_manufacturer = models.CharField(max_length=200, default="RUCKUS", blank=True)

    # --- Venue mapping config (neu) ---
    venue_mapping_mode = models.CharField(
        max_length=20,
        choices=VENUE_MAPPING_CHOICES,
        default=VENUE_MAPPING_SITES,
    )

    venue_child_location_name = models.CharField(
        max_length=100,
        blank=True,
        default="Venue",
        help_text="Used only when mapping mode is 'both' (child location name under the venue site).",
    )

    venue_locations_parent_site = models.ForeignKey(
        to=Site,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="ruckus_r1_sync_parent_site_configs",
        help_text="Required only when mapping mode is 'locations'. Devices will be placed in this site and the venue becomes a Location.",
    )

    last_sync = models.DateTimeField(null=True, blank=True)
    last_sync_status = models.CharField(max_length=32, default="never", blank=True)
    last_sync_message = models.TextField(default="", blank=True)

    custom_field_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("tenant__name",)
        verbose_name = "RUCKUS R1 Tenant Config"
        verbose_name_plural = "RUCKUS R1 Tenant Configs"

    def __str__(self) -> str:
        return f"{self.name} (Mandant: {self.tenant})"

    def get_absolute_url(self):
        # IMPORTANT: must match urls.py name
        return reverse("plugins:ruckus_r1_sync:ruckusr1tenantconfig", kwargs={"pk": self.pk})


class RuckusR1SyncLog(NetBoxModel):
    STATUS_CHOICES = (
        ("success", "success"),
        ("failed", "failed"),
        ("skipped", "skipped"),
        ("running", "running"),
        ("unknown", "unknown"),
    )

    tenant = models.ForeignKey(
        to=Tenant,
        on_delete=models.CASCADE,
        related_name="ruckus_r1_sync_logs",
    )

    started = models.DateTimeField(auto_now_add=False, null=False)
    finished = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="unknown")
    summary = models.TextField(default="", blank=False)

    venues = models.IntegerField(default=0)
    networks = models.IntegerField(default=0)
    devices = models.IntegerField(default=0)
    interfaces = models.IntegerField(default=0)
    macs = models.IntegerField(default=0)
    vlans = models.IntegerField(default=0)
    ips = models.IntegerField(default=0)
    wlans = models.IntegerField(default=0)
    wlan_groups = models.IntegerField(default=0)
    tunnels = models.IntegerField(default=0)
    cables = models.IntegerField(default=0)
    clients = models.IntegerField(default=0)

    error = models.TextField(default="", blank=False)
    message = models.TextField(default="", blank=False)

    custom_field_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-created",)
        verbose_name = "RUCKUS R1 Sync Log"
        verbose_name_plural = "RUCKUS R1 Sync Logs"

    def __str__(self) -> str:
        return f"{self.tenant} {self.status} ({self.created})"

    def get_absolute_url(self):
        return reverse("plugins:ruckus_r1_sync:ruckusr1synclog_list")


class RuckusR1Client(NetBoxModel):
    tenant = models.ForeignKey(
        to=Tenant,
        on_delete=models.CASCADE,
        related_name="ruckus_r1_clients",
    )

    venue_id = models.CharField(max_length=128, blank=True, default="")
    network_id = models.CharField(max_length=128, blank=True, default="")

    ruckus_id = models.CharField(max_length=128, blank=True, default="")

    mac = models.CharField(max_length=32, db_index=True)
    ip_address = models.CharField(max_length=64, blank=True, default="")
    hostname = models.CharField(max_length=255, blank=True, default="")
    vlan = models.IntegerField(null=True, blank=True)
    ssid = models.CharField(max_length=128, blank=True, default="")
    last_seen = models.DateTimeField(null=True, blank=True)

    raw = models.JSONField(default=dict, blank=True)
    custom_field_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("tenant__name", "mac")
        verbose_name = "RUCKUS R1 Client"
        verbose_name_plural = "RUCKUS R1 Clients"
        constraints = [
            models.UniqueConstraint(fields=["tenant", "mac"], name="ruckus_r1_client_tenant_mac_uniq")
        ]

    def __str__(self) -> str:
        return f"{self.mac} ({self.tenant})"

    def get_absolute_url(self):
        return reverse("plugins:ruckus_r1_sync:ruckusr1client_list")
