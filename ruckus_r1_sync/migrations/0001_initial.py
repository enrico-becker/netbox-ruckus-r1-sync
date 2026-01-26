from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("tenancy", "0001_initial"),
        # extras enthält u.a. die Tag-Infrastruktur (falls du später tags nutzt)
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
                ("api_base_url", models.URLField(help_text="e.g. Asia	https://api.asia.ruckus.cloud - Europe	https://api.eu.ruckus.cloud - North America	https://api.ruckus.cloud")),
                ("ruckus_tenant_id", models.CharField(help_text="R1 Tenant ID for /oauth2/token/<ruckusTenantId>", max_length=128)),
                ("client_id", models.CharField(max_length=256)),
                ("client_secret", models.CharField(max_length=256)),
                ("enabled", models.BooleanField(default=True)),

                ("allow_stub_devices", models.BooleanField(default=True)),
                ("allow_stub_vlans", models.BooleanField(default=True)),
                ("allow_stub_wireless", models.BooleanField(default=True)),

                ("authoritative_devices", models.BooleanField(default=False)),
                ("authoritative_interfaces", models.BooleanField(default=False)),
                ("authoritative_ips", models.BooleanField(default=False)),
                ("authoritative_vlans", models.BooleanField(default=False)),
                ("authoritative_wireless", models.BooleanField(default=False)),
                ("authoritative_cabling", models.BooleanField(default=False)),

                ("default_site_group", models.CharField(blank=True, default="", max_length=200)),
                ("default_device_role", models.CharField(blank=True, default="Switch/AP", max_length=200)),
                ("default_manufacturer", models.CharField(blank=True, default="RUCKUS", max_length=200)),

                ("last_sync", models.DateTimeField(blank=True, null=True)),
                ("last_sync_status", models.CharField(blank=True, default="", max_length=32)),
                ("last_sync_message", models.TextField(blank=True, default="")),

                ("tenant", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="ruckus_r1_config",
                    to="tenancy.tenant"
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
                    to="tenancy.tenant"
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
                ("ap_serial", models.CharField(blank=True, default="", max_length=128)),

                ("mac", models.CharField(db_index=True, max_length=32)),
                ("ip", models.CharField(blank=True, default="", max_length=64)),
                ("hostname", models.CharField(blank=True, default="", max_length=255)),
                ("vlan", models.IntegerField(blank=True, null=True)),
                ("ssid", models.CharField(blank=True, default="", max_length=128)),
                ("last_seen", models.DateTimeField(blank=True, null=True)),

                ("raw", models.JSONField(blank=True, default=dict)),

                ("tenant", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="ruckus_r1_clients",
                    to="tenancy.tenant"
                )),
            ],
            options={
                "verbose_name": "RUCKUS R1 Client",
                "verbose_name_plural": "RUCKUS R1 Clients",
                "unique_together": {("tenant", "mac")},
            },
        ),
    ]
 