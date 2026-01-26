from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ("ruckus_r1_sync", "0002_add_custom_field_data"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE ruckus_r1_sync_ruckusr1synclog
                    ADD COLUMN IF NOT EXISTS started timestamptz;
                ALTER TABLE ruckus_r1_sync_ruckusr1synclog
                    ADD COLUMN IF NOT EXISTS finished timestamptz;

                ALTER TABLE ruckus_r1_sync_ruckusr1synclog
                    ALTER COLUMN started SET DEFAULT now();

                UPDATE ruckus_r1_sync_ruckusr1synclog
                   SET started = COALESCE(started, created, now())
                 WHERE started IS NULL;

                ALTER TABLE ruckus_r1_sync_ruckusr1synclog
                    ALTER COLUMN started SET NOT NULL;
            """,
            reverse_sql="""
                ALTER TABLE ruckus_r1_sync_ruckusr1synclog
                    ALTER COLUMN started DROP DEFAULT;
            """,
        ),
    ]
 