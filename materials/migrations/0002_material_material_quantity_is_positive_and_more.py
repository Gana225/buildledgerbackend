from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("materials", "0001_initial")]

    operations = [
        migrations.AddConstraint(
            model_name="material",
            constraint=models.CheckConstraint(
                condition=models.Q(("quantity__gt", 0)),
                name="material_quantity_is_positive",
            ),
        ),
        migrations.AddConstraint(
            model_name="material",
            constraint=models.CheckConstraint(
                condition=models.Q(("price__gte", 0)),
                name="material_price_is_not_negative",
            ),
        ),
    ]
