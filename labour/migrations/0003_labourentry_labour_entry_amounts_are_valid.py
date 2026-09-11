from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("labour", "0002_labourassignment_and_more")]

    operations = [
        migrations.AddConstraint(
            model_name="labourentry",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(("wage__gte", 0))
                    & models.Q(("paid_amount__gte", 0))
                    & models.Q(("paid_amount__lte", models.F("wage")))
                ),
                name="labour_entry_amounts_are_valid",
            ),
        ),
    ]
