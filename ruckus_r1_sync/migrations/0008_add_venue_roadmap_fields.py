from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ruckus_r1_sync", "0007_add_venue_mapping_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="ruckusr1tenantconfig",
            name="venues_cache",
            field=models.JSONField(
                default=list,
                blank=True,
                help_text="Cached Venues from RUCKUS One (list of {id,name}). Use 'Refresh Venues' button to update.",
            ),
        ),
        migrations.AddField(
            model_name="ruckusr1tenantconfig",
            name="venues_selected",
            field=models.JSONField(
                default=list,
                blank=True,
                help_text="Venue IDs selected for sync. Empty list means: sync ALL venues.",
            ),
        ),
    ]
