import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def copy_existing_labour_data(apps, schema_editor):
    Labour = apps.get_model("labour", "Labour")
    LabourEntry = apps.get_model("labour", "LabourEntry")
    LabourAssignment = apps.get_model("labour", "LabourAssignment")

    for labour in Labour.objects.select_related("site").all():
        Labour.objects.filter(pk=labour.pk).update(user_id=labour.site.user_id)
        LabourAssignment.objects.create(
            labour_id=labour.pk,
            site_id=labour.site_id,
            start_date=labour.created_at.date(),
        )

    for entry in LabourEntry.objects.select_related("labour").all():
        LabourEntry.objects.filter(pk=entry.pk).update(site_id=entry.labour.site_id)


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial"), ("labour", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="LabourAssignment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("start_date", models.DateField()),
                ("end_date", models.DateField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("labour", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assignments", to="labour.labour")),
                ("site", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="labour_assignments", to="sites.site")),
            ],
            options={"ordering": ["-start_date", "-id"]},
        ),
        migrations.RemoveConstraint(model_name="labour", name="unique_labour_name_per_site"),
        migrations.AddField(model_name="labour", name="user", field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name="labours", to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name="labourentry", name="site", field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name="labour_entries", to="sites.site")),
        migrations.RunPython(copy_existing_labour_data, migrations.RunPython.noop),
        migrations.RemoveField(model_name="labour", name="site"),
        migrations.AlterField(model_name="labour", name="user", field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="labours", to=settings.AUTH_USER_MODEL)),
        migrations.AlterField(model_name="labourentry", name="site", field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="labour_entries", to="sites.site")),
        migrations.AddConstraint(model_name="labour", constraint=models.UniqueConstraint(fields=("user", "name"), name="unique_labour_name_per_user")),
        migrations.AddConstraint(model_name="labourassignment", constraint=models.UniqueConstraint(fields=("labour", "site", "start_date"), name="unique_labour_assignment_start")),
    ]
