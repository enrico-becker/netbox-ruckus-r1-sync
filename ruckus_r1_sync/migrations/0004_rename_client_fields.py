from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("ruckus_r1_sync", "0003_add_message_to_synclog"),
    ]

    operations = [
        migrations.RenameField(
            model_name="ruckusr1client",
            old_name="ip",
            new_name="ip_address",
        ),
        migrations.RenameField(
            model_name="ruckusr1client",
            old_name="ap_serial",
            new_name="ruckus_id",
        ),
    ]
 