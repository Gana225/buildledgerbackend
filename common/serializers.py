from rest_framework import serializers


class ExpenseCategorySerializer(
    serializers.Serializer
):
    total = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    paid = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    remaining = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

class MaterialAccountingSerializer(
    serializers.Serializer
):
    total = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )


class SiteAccountingSerializer(
    serializers.Serializer
):
    labour = ExpenseCategorySerializer()
    mesthiri = ExpenseCategorySerializer()

    materials = MaterialAccountingSerializer()

    total_expense = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    total_paid = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    total_outstanding = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )        
        
class DashboardSiteInfoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    code = serializers.CharField()
    name = serializers.CharField()


class ExpenseBreakdownSerializer(serializers.Serializer):
    category = serializers.CharField()

    amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )


class DailyLabourSerializer(serializers.Serializer):
    date = serializers.DateField()

    total = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    paid = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )


class DailyMesthiriSerializer(serializers.Serializer):
    date = serializers.DateField()

    total = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    paid = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )


class DailyMaterialSerializer(serializers.Serializer):
    purchase_date = serializers.DateField()

    total = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )


class MonthlyExpenseSerializer(serializers.Serializer):
    month = serializers.DateField()

    total = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )


class SiteDashboardSerializer(serializers.Serializer):
    site = DashboardSiteInfoSerializer()

    summary = SiteAccountingSerializer()

    expense_breakdown = ExpenseBreakdownSerializer(
        many=True
    )

    labour_daily = DailyLabourSerializer(
        many=True
    )

    mesthiri_daily = DailyMesthiriSerializer(
        many=True
    )

    material_daily = DailyMaterialSerializer(
        many=True
    )

    labour_monthly = MonthlyExpenseSerializer(
        many=True
    )

    mesthiri_monthly = MonthlyExpenseSerializer(
        many=True
    )

    material_monthly = MonthlyExpenseSerializer(
        many=True
    )


class MainDashboardSummarySerializer(serializers.Serializer):
    labour = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    mesthiri = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    materials = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    total_expense = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    total_paid = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    total_outstanding = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )


class SiteComparisonSerializer(serializers.Serializer):
    site_id = serializers.IntegerField()
    site_code = serializers.CharField()
    site_name = serializers.CharField()

    total_expense = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    total_paid = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    total_outstanding = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )


class MainDashboardSerializer(serializers.Serializer):
    site_count = serializers.IntegerField()

    summary = MainDashboardSummarySerializer()

    expense_breakdown = ExpenseBreakdownSerializer(
        many=True
    )

    sites = SiteComparisonSerializer(
        many=True
    )