from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ruckus_r1_sync", "0005_client_venue_network_defaults"),  # <-- ggf. anpassen!
    ]

    operations = [
        migrations.AddField(
            model_name="ruckusr1tenantconfig",
            name="sync_wlans",
            field=models.BooleanField(default=True, verbose_name="Sync WLANs (SSIDs)"),
        ),
        migrations.AddField(
            model_name="ruckusr1tenantconfig",
            name="sync_vlans",
            field=models.BooleanField(default=True, verbose_name="Sync VLANs"),
        ),
        migrations.AddField(
            model_name="ruckusr1tenantconfig",
            name="sync_aps",
            field=models.BooleanField(default=True, verbose_name="Sync Access Points"),
        ),
        migrations.AddField(
            model_name="ruckusr1tenantconfig",
            name="sync_switches",
            field=models.BooleanField(default=True, verbose_name="Sync Switches"),
        ),
        migrations.AddField(
            model_name="ruckusr1tenantconfig",
            name="sync_wifi_clients",
            field=models.BooleanField(default=True, verbose_name="Sync Wi-Fi clients"),
        ),
        migrations.AddField(
            model_name="ruckusr1tenantconfig",
            name="sync_wired_clients",
            field=models.BooleanField(default=True, verbose_name="Sync wired clients"),
        ),
        migrations.AddField(
            model_name="ruckusr1tenantconfig",
            name="sync_interfaces",
            field=models.BooleanField(default=True, verbose_name="Sync interfaces (e.g. switch ports)"),
        ),
        migrations.AddField(
            model_name="ruckusr1tenantconfig",
            name="sync_cabling",
            field=models.BooleanField(default=True, verbose_name="Sync cabling (wired links)"),
        ),
        migrations.AddField(
            model_name="ruckusr1tenantconfig",
            name="sync_wireless_links",
            field=models.BooleanField(default=True, verbose_name="Sync wireless links (mesh/topology)"),
        ),
    ]
