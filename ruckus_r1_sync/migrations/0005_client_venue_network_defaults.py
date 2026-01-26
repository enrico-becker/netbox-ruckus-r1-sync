# ruckus_r1_sync/migrations/0005_client_venue_network_defaults.py
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ruckus_r1_sync", "0004_rename_client_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ruckusr1client",
            name="venue_id",
            field=models.CharField(max_length=128, blank=True, default=""),
        ),
        migrations.AlterField(
            model_name="ruckusr1client",
            name="network_id",
            field=models.CharField(max_length=128, blank=True, default=""),
        ),
    ]
 