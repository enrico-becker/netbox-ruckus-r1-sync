from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("dcim", "0001_initial"),
        ("ruckus_r1_sync", "0006_sync_toggles"),
    ]

    operations = [
        migrations.AddField(
            model_name="ruckusr1tenantconfig",
            name="venue_mapping_mode",
            field=models.CharField(
                choices=[
                    ("sites", "Sites (Venue \u2192 Site)"),
                    ("locations", "Locations (Venue \u2192 Location under Parent Site)"),
                    ("both", "Both (Venue \u2192 Site + child Location)"),
                ],
                default="sites",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="ruckusr1tenantconfig",
            name="venue_child_location_name",
            field=models.CharField(
                blank=True,
                default="Venue",
                help_text="Used only when mapping mode is 'both' (child location name under the venue site).",
                max_length=100,
            ),
        ),
        migrations.AddField(
            model_name="ruckusr1tenantconfig",
            name="venue_locations_parent_site",
            field=models.ForeignKey(
                blank=True,
                help_text="Required only when mapping mode is 'locations'. Devices will be placed in this site and the venue becomes a Location.",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="ruckus_r1_sync_parent_site_configs",
                to="dcim.site",
            ),
        ),
    ]
