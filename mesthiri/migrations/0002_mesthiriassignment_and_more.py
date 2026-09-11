import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def copy_existing_mesthiri_data(apps, schema_editor):
    Mesthiri = apps.get_model("mesthiri", "Mesthiri")
    MesthiriEntry = apps.get_model("mesthiri", "MesthiriEntry")
    MesthiriAssignment = apps.get_model("mesthiri", "MesthiriAssignment")

    for mesthiri in Mesthiri.objects.select_related("site").all():
        Mesthiri.objects.filter(pk=mesthiri.pk).update(user_id=mesthiri.site.user_id)
        MesthiriAssignment.objects.create(
            mesthiri_id=mesthiri.pk,
            site_id=mesthiri.site_id,
            start_date=mesthiri.created_at.date(),
        )

    for entry in MesthiriEntry.objects.select_related("mesthiri").all():
        MesthiriEntry.objects.filter(pk=entry.pk).update(site_id=entry.mesthiri.site_id)


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial"), ("mesthiri", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="MesthiriAssignment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("start_date", models.DateField()),
                ("end_date", models.DateField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("mesthiri", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assignments", to="mesthiri.mesthiri")),
                ("site", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="mesthiri_assignments", to="sites.site")),
            ],
            options={"ordering": ["-start_date", "-id"]},
        ),
        migrations.RemoveConstraint(model_name="mesthiri", name="unique_mesthiri_name_per_site"),
        migrations.AddField(model_name="mesthiri", name="user", field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name="mesthiris", to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name="mesthirientry", name="site", field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name="mesthiri_entries", to="sites.site")),
        migrations.RunPython(copy_existing_mesthiri_data, migrations.RunPython.noop),
        migrations.RemoveField(model_name="mesthiri", name="site"),
        migrations.AlterField(model_name="mesthiri", name="user", field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="mesthiris", to=settings.AUTH_USER_MODEL)),
        migrations.AlterField(model_name="mesthirientry", name="site", field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="mesthiri_entries", to="sites.site")),
        migrations.AddConstraint(model_name="mesthiri", constraint=models.UniqueConstraint(fields=("user", "name"), name="unique_mesthiri_name_per_user")),
        migrations.AddConstraint(model_name="mesthiriassignment", constraint=models.UniqueConstraint(fields=("mesthiri", "site", "start_date"), name="unique_mesthiri_assignment_start")),
    ]
