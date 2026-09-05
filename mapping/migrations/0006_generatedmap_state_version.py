from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mapping", "0005_merge_20251025_1752"),
    ]

    operations = [
        migrations.AddField(
            model_name="generatedmap",
            name="state_version",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="状态版本"),
        ),
    ]
