from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("mesthiri", "0002_mesthiriassignment_and_more")]

    operations = [
        migrations.AddConstraint(
            model_name="mesthirientry",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(("wage__gte", 0))
                    & models.Q(("paid_amount__gte", 0))
                    & models.Q(("paid_amount__lte", models.F("wage")))
                ),
                name="mesthiri_entry_amounts_are_valid",
            ),
        ),
    ]
