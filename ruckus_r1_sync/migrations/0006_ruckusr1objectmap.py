from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("ruckus_r1_sync", "0001_initial"),  # adjust if your latest migration differs
        ("contenttypes", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="RuckusR1ObjectMap",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("custom_field_data", models.JSONField(blank=True, default=dict)),
                ("object_type", models.CharField(choices=[("venue", "Venue"), ("device", "Device"), ("vlan", "VLAN"), ("wlan", "WLAN"), ("interface", "Interface")], max_length=32)),
                ("r1_key", models.CharField(help_text="Stable RUCKUS One identifier (or composite key)", max_length=256)),
                ("netbox_object_id", models.PositiveBigIntegerField()),
                ("last_seen", models.DateTimeField(blank=True, null=True)),
                ("last_r1_name", models.CharField(blank=True, default="", max_length=200)),
                ("netbox_content_type", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="+", to="contenttypes.contenttype")),
                ("tenant_config", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="object_maps", to="ruckus_r1_sync.ruckusr1tenantconfig")),
            ],
            options={
                "ordering": ("tenant_config", "object_type", "r1_key"),
            },
        ),
        migrations.AddConstraint(
            model_name="ruckusr1objectmap",
            constraint=models.UniqueConstraint(fields=("tenant_config", "object_type", "r1_key"), name="ruckus_r1_objectmap_unique_key"),
        ),
    ]
