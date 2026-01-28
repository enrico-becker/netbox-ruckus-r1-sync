from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("dcim", "0001_initial"),
        ("tenancy", "0001_initial"),
        ("extras", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="RuckusR1TenantConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),

                # NetBoxModel expects this
                ("custom_field_data", models.JSONField(blank=True, default=dict)),

                ("name", models.CharField(blank=True, default="", max_length=200)),
                ("api_base_url", models.URLField(help_text="e.g. Asia\thttps://api.asia.ruckus.cloud - Europe\thttps://api.eu.ruckus.cloud - North America\thttps://api.ruckus.cloud")),
                ("ruckus_tenant_id", models.CharField(help_text="R1 Tenant ID for /oauth2/token/<ruckusTenantId>", max_length=128)),
                ("client_id", models.CharField(max_length=256)),
                ("client_secret", models.CharField(max_length=256)),
                ("enabled", models.BooleanField(default=True)),

                # Sync scope toggles
                ("sync_wlans", models.BooleanField(default=True, verbose_name="Sync WLANs (SSIDs)")),
                ("sync_vlans", models.BooleanField(default=True, verbose_name="Sync VLANs")),
                ("sync_aps", models.BooleanField(default=True, verbose_name="Sync Access Points")),
                ("sync_switches", models.BooleanField(default=True, verbose_name="Sync Switches")),
                ("sync_wifi_clients", models.BooleanField(default=True, verbose_name="Sync Wi-Fi clients")),
                ("sync_wired_clients", models.BooleanField(default=True, verbose_name="Sync wired clients")),
                ("sync_interfaces", models.BooleanField(default=True, verbose_name="Sync interfaces (e.g. switch ports)")),
                ("sync_cabling", models.BooleanField(default=True, verbose_name="Sync cabling (wired links)")),
                ("sync_wireless_links", models.BooleanField(default=True, verbose_name="Sync wireless links (mesh/topology)")),

                # Allow creating stub/placeholder objects in NetBox
                ("allow_stub_devices", models.BooleanField(default=True)),
                ("allow_stub_vlans", models.BooleanField(default=True)),
                ("allow_stub_wireless", models.BooleanField(default=True)),

                # If enabled, objects in these categories will be treated as authoritative from RUCKUS One
                ("authoritative_devices", models.BooleanField(default=False)),
                ("authoritative_interfaces", models.BooleanField(default=False)),
                ("authoritative_ips", models.BooleanField(default=False)),
                ("authoritative_vlans", models.BooleanField(default=False)),
                ("authoritative_wireless", models.BooleanField(default=False)),
                ("authoritative_cabling", models.BooleanField(default=False)),

                ("default_site_group", models.CharField(blank=True, default="", max_length=200)),
                ("default_device_role", models.CharField(blank=True, default="Switch/AP", max_length=200)),
                ("default_manufacturer", models.CharField(blank=True, default="RUCKUS", max_length=200)),

                # Venue mapping / roadmap
                ("venue_mapping_mode", models.CharField(
                    choices=[
                        ("sites", "Sites (Venue → Site)"),
                        ("locations", "Locations (Venue → Location under Parent Site)"),
                        ("both", "Both (Venue → Site + child Location)"),
                    ],
                    default="sites",
                    max_length=20,
                )),
                ("venue_child_location_name", models.CharField(
                    blank=True,
                    default="Venue",
                    help_text="Used only when mapping mode is 'both' (child location name under the venue site).",
                    max_length=100,
                )),
                ("venue_locations_parent_site", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="ruckus_r1_sync_parent_site_configs",
                    help_text="Required only when mapping mode is 'locations'. Devices will be placed in this site and the venue becomes a Location.",
                    to="dcim.site",
                )),
                ("venues_cache", models.JSONField(
                    default=list,
                    blank=True,
                    help_text="Cached Venues from RUCKUS One (list of {id,name}). Use 'Refresh Venues' button to update.",
                )),
                ("venues_selected", models.JSONField(
                    default=list,
                    blank=True,
                    help_text="Venue IDs selected for sync. Empty list means: sync ALL venues.",
                )),

                ("last_sync", models.DateTimeField(blank=True, null=True)),
                ("last_sync_status", models.CharField(blank=True, default="", max_length=32)),
                ("last_sync_message", models.TextField(blank=True, default="")),

                ("tenant", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="ruckus_r1_config",
                    to="tenancy.tenant",
                )),
            ],
            options={
                "verbose_name": "RUCKUS R1 Tenant Config",
                "verbose_name_plural": "RUCKUS R1 Tenant Configs",
            },
        ),

        migrations.CreateModel(
            name="RuckusR1SyncLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),

                # NetBoxModel expects this
                ("custom_field_data", models.JSONField(blank=True, default=dict)),

                ("started", models.DateTimeField(default=django.utils.timezone.now)),
                ("finished", models.DateTimeField(blank=True, null=True)),
                ("status", models.CharField(default="running", max_length=32)),
                ("summary", models.TextField(blank=True, default="")),

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

                ("error", models.TextField(blank=True, default="")),

                ("tenant", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="ruckus_r1_sync_logs",
                    to="tenancy.tenant",
                )),
            ],
            options={
                "ordering": ("-started",),
                "verbose_name": "RUCKUS R1 Sync Log",
                "verbose_name_plural": "RUCKUS R1 Sync Logs",
            },
        ),

        migrations.CreateModel(
            name="RuckusR1Client",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),

                # NetBoxModel expects this
                ("custom_field_data", models.JSONField(blank=True, default=dict)),

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

                ("tenant", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="ruckus_r1_clients",
                    to="tenancy.tenant",
                )),
            ],
            options={
                "verbose_name": "RUCKUS R1 Client",
                "verbose_name_plural": "RUCKUS R1 Clients",
                "unique_together": {("tenant", "mac")},
            },
        ),
    ]
