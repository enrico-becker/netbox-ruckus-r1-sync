from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("tenancy", "0001_initial"),
        ("dcim", "0001_initial"),
        ("contenttypes", "0001_initial"),
    ]

    operations = [

        # -------------------------------------------------
        # RuckusR1TenantConfig
        # -------------------------------------------------
        migrations.CreateModel(
            name="RuckusR1TenantConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=200)),
                ("api_base_url", models.CharField(
                    default="https://api.eu.ruckus.cloud",
                    max_length=200,
                    help_text="RUCKUS Cloud API base URL",
                )),
                ("ruckus_tenant_id", models.CharField(max_length=128)),
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

                ("venue_mapping_mode", models.CharField(
                    max_length=20,
                    default="sites",
                    choices=[
                        ("sites", "Sites (Venue → Site)"),
                        ("locations", "Locations (Venue → Location under Parent Site)"),
                        ("both", "Both (Venue → Site + child Location)"),
                    ],
                )),
                ("venue_child_location_name", models.CharField(
                    blank=True,
                    default="Venue",
                    max_length=100,
                )),
                ("venues_cache", models.JSONField(blank=True, default=list)),
                ("venues_selected", models.JSONField(blank=True, default=list)),

                ("last_sync", models.DateTimeField(blank=True, null=True)),
                ("last_sync_status", models.CharField(blank=True, default="never", max_length=32)),
                ("last_sync_message", models.TextField(blank=True, default="")),

                ("custom_field_data", models.JSONField(blank=True, default=dict)),

                ("tenant", models.OneToOneField(
                    to="tenancy.tenant",
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="ruckus_r1_sync_config",
                )),
                ("venue_locations_parent_site", models.ForeignKey(
                    blank=True,
                    null=True,
                    to="dcim.site",
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="ruckus_r1_sync_parent_site_configs",
                )),
            ],
            options={
                "ordering": ("tenant__name",),
            },
        ),

        # -------------------------------------------------
        # RuckusR1SyncLog
        # -------------------------------------------------
        migrations.CreateModel(
            name="RuckusR1SyncLog",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("started", models.DateTimeField()),
                ("finished", models.DateTimeField(blank=True, null=True)),
                ("status", models.CharField(max_length=32, default="unknown")),
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
                ("tenant", models.ForeignKey(
                    to="tenancy.tenant",
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="ruckus_r1_sync_logs",
                )),
            ],
            options={"ordering": ("-created",)},
        ),

        # -------------------------------------------------
        # RuckusR1Client
        # -------------------------------------------------
        migrations.CreateModel(
            name="RuckusR1Client",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("venue_id", models.CharField(blank=True, default="", max_length=128)),
                ("network_id", models.CharField(blank=True, default="", max_length=128)),
                ("ruckus_id", models.CharField(blank=True, default="", max_length=128)),
                ("mac", models.CharField(max_length=32, db_index=True)),
                ("ip_address", models.CharField(blank=True, default="", max_length=64)),
                ("hostname", models.CharField(blank=True, default="", max_length=255)),
                ("vlan", models.IntegerField(blank=True, null=True)),
                ("ssid", models.CharField(blank=True, default="", max_length=128)),
                ("last_seen", models.DateTimeField(blank=True, null=True)),
                ("raw", models.JSONField(blank=True, default=dict)),
                ("custom_field_data", models.JSONField(blank=True, default=dict)),
                ("tenant", models.ForeignKey(
                    to="tenancy.tenant",
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="ruckus_r1_clients",
                )),
            ],
        ),

        migrations.AddConstraint(
            model_name="ruckusr1client",
            constraint=models.UniqueConstraint(
                fields=("tenant", "mac"),
                name="ruckus_r1_client_tenant_mac_uniq",
            ),
        ),

        # -------------------------------------------------
        # RuckusR1ObjectMap  (JETZT INTEGRIERT)
        # -------------------------------------------------
        migrations.CreateModel(
            name="RuckusR1ObjectMap",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("object_type", models.CharField(
                    max_length=32,
                    choices=[
                        ("venue", "Venue"),
                        ("device", "Device"),
                        ("vlan", "VLAN"),
                        ("wlan", "WLAN"),
                        ("interface", "Interface"),
                    ],
                )),
                ("r1_key", models.CharField(max_length=256)),
                ("netbox_object_id", models.PositiveBigIntegerField()),
                ("last_seen", models.DateTimeField(blank=True, null=True)),
                ("last_r1_name", models.CharField(blank=True, default="", max_length=200)),
                ("custom_field_data", models.JSONField(blank=True, default=dict)),
                ("netbox_content_type", models.ForeignKey(
                    to="contenttypes.contenttype",
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="+",
                )),
                ("tenant_config", models.ForeignKey(
                    to="ruckus_r1_sync.ruckusr1tenantconfig",
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="object_maps",
                )),
            ],
            options={
                "ordering": ("tenant_config", "object_type", "r1_key"),
            },
        ),

        migrations.AddConstraint(
            model_name="ruckusr1objectmap",
            constraint=models.UniqueConstraint(
                fields=("tenant_config", "object_type", "r1_key"),
                name="ruckus_r1_objectmap_unique_key",
            ),
        ),
    ]
