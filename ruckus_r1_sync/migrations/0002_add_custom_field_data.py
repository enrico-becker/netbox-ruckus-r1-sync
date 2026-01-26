from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ruckus_r1_sync", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="ruckusr1tenantconfig",
            name="custom_field_data",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="ruckusr1synclog",
            name="custom_field_data",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="ruckusr1client",
            name="custom_field_data",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
 