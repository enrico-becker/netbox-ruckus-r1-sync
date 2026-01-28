from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("tenancy", "0001_initial"),
        ("dcim", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="RuckusR1TenantConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=200)),
                (
                    "api_base_url",
                    models.CharField(
                        default="https://api.eu.ruckus.cloud",
                        help_text="RUCKUS Cloud API base URL (example: https://api.eu.ruckus.cloud)",
                        max_length=200,
                    ),
                ),
                (
                    "ruckus_tenant_id",
                    models.CharField(
                        help_text="RUCKUS Cloud tenantId used for token endpoint /oauth2/token/<tenantId>",
                        max_length=128,
                    ),
                ),
                ("client_id", models.CharField(max_length=256)),
                ("client_secret", models.CharField(max_length=256)),
                ("enabled", models.BooleanField(default=True)),
                ("allow_stub_devices", models.BooleanField(default=True)),
                ("allow_stub_vlans", models.BooleanField(default=True)),
                ("allow_stub_wireless", models.BooleanField(default=True)),
                ("sync_wlans", models.BooleanField(default=True)),
                ("sync_aps", models.BooleanField(default=True)),
                ("sync_switches", models.BooleanField(default=True)),
                ("sync_interfaces", models.BooleanField(default=True)),
                ("sync_wifi_clients", models.BooleanField(default=True)),
                ("sync_wired_clients", models.BooleanField(default=True)),
                ("sync_cabling", models.BooleanField(default=True)),
                ("sync_wireless_links", models.BooleanField(default=True)),
                ("sync_vlans", models.BooleanField(default=False)),
                ("authoritative_devices", models.BooleanField(default=False)),
                ("authoritative_interfaces", models.BooleanField(default=False)),
                ("authoritative_ips", models.BooleanField(default=False)),
                ("authoritative_vlans", models.BooleanField(default=False)),
                ("authoritative_wireless", models.BooleanField(default=False)),
                ("authoritative_cabling", models.BooleanField(default=False)),
                ("default_site_group", models.CharField(blank=True, default="", max_length=200)),
                ("default_device_role", models.CharField(blank=True, default="", max_length=200)),
                ("default_manufacturer", models.CharField(blank=True, default="RUCKUS", max_length=200)),
                (
                    "venue_mapping_mode",
                    models.CharField(
                        choices=[("sites", "Sites (Venue → Site)"), ("locations", "Locations (Venue → Location under Parent Site)"), ("both", "Both (Venue → Site + child Location)")],
                        default="sites",
                        max_length=20,
                    ),
                ),
                (
                    "venue_child_location_name",
                    models.CharField(
                        blank=True,
                        default="Venue",
                        help_text="Used only when mapping mode is 'both' (child location name under the venue site).",
                        max_length=100,
                    ),
                ),
                (
                    "venues_cache",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="Cached Venues from RUCKUS One (list of {id,name}). Use 'Refresh Venues' button to update.",
                    ),
                ),
                (
                    "venues_selected",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="Venue IDs selected for sync. Empty list means: sync ALL venues.",
                    ),
                ),
                ("last_sync", models.DateTimeField(blank=True, null=True)),
                ("last_sync_status", models.CharField(blank=True, default="never", max_length=32)),
                ("last_sync_message", models.TextField(blank=True, default="")),
                ("custom_field_data", models.JSONField(blank=True, default=dict)),
                (
                    "tenant",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ruckus_r1_sync_config",
                        to="tenancy.tenant",
                        unique=True,
                    ),
                ),
                (
                    "venue_locations_parent_site",
                    models.ForeignKey(
                        blank=True,
                        help_text="Required only when mapping mode is 'locations'. Devices will be placed in this site and the venue becomes a Location.",
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="ruckus_r1_sync_parent_site_configs",
                        to="dcim.site",
                    ),
                ),
            ],
            options={
                "verbose_name": "RUCKUS R1 Tenant Config",
                "verbose_name_plural": "RUCKUS R1 Tenant Configs",
                "ordering": ("tenant__name",),
            },
        ),
        migrations.CreateModel(
            name="RuckusR1SyncLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("started", models.DateTimeField()),
                ("finished", models.DateTimeField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("success", "success"), ("failed", "failed"), ("skipped", "skipped"), ("running", "running"), ("unknown", "unknown")],
                        default="unknown",
                        max_length=32,
                    ),
                ),
                ("summary", models.TextField(default="")),
                ("venues", models.IntegerField(default=0)),
                ("networks", models.IntegerField(default=0)),
                ("devices", models.IntegerField(default=0)),
                ("interfaces", models.IntegerField(default=0)),
                ("macs", models.IntegerField(default=0)),
                ("vlans", models.IntegerField(default=0)),
                ("ips", models.IntegerField(default=0)),
                ("wlans", models.IntegerField(default=0)),
                ("wlan_groups", models.IntegerField(default=0)),
                ("tunnels", models.IntegerField(default=0)),
                ("cables", models.IntegerField(default=0)),
                ("clients", models.IntegerField(default=0)),
                ("error", models.TextField(default="")),
                ("message", models.TextField(default="")),
                ("custom_field_data", models.JSONField(blank=True, default=dict)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ruckus_r1_sync_logs",
                        to="tenancy.tenant",
                    ),
                ),
            ],
            options={
                "verbose_name": "RUCKUS R1 Sync Log",
                "verbose_name_plural": "RUCKUS R1 Sync Logs",
                "ordering": ("-created",),
            },
        ),
        migrations.CreateModel(
            name="RuckusR1Client",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("venue_id", models.CharField(blank=True, default="", max_length=128)),
                ("network_id", models.CharField(blank=True, default="", max_length=128)),
                ("ruckus_id", models.CharField(blank=True, default="", max_length=128)),
                ("mac", models.CharField(db_index=True, max_length=32)),
                ("ip_address", models.CharField(blank=True, default="", max_length=64)),
                ("hostname", models.CharField(blank=True, default="", max_length=255)),
                ("vlan", models.IntegerField(blank=True, null=True)),
                ("ssid", models.CharField(blank=True, default="", max_length=128)),
                ("last_seen", models.DateTimeField(blank=True, null=True)),
                ("raw", models.JSONField(blank=True, default=dict)),
                ("custom_field_data", models.JSONField(blank=True, default=dict)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ruckus_r1_clients",
                        to="tenancy.tenant",
                    ),
                ),
            ],
            options={
                "verbose_name": "RUCKUS R1 Client",
                "verbose_name_plural": "RUCKUS R1 Clients",
                "ordering": ("tenant__name", "mac"),
            },
        ),
        migrations.AddConstraint(
            model_name="ruckusr1client",
            constraint=models.UniqueConstraint(fields=("tenant", "mac"), name="ruckus_r1_client_tenant_mac_uniq"),
        ),
    ]
