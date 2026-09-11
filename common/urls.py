from django.urls import path

from .views import (
    SiteAccountingView,
    MainDashboardView,
    SiteDashboardView,
)


urlpatterns = [
    path(
        "sites/<int:pk>/accounting/",
        SiteAccountingView.as_view(),
        name="site-accounting",
    ),

    path(
        "dashboard/",
        MainDashboardView.as_view(),
        name="main-dashboard",
    ),

    path(
        "sites/<int:site_id>/dashboard/",
        SiteDashboardView.as_view(),
        name="site-dashboard",
    ),
]