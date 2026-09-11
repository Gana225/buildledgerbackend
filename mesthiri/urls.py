from django.urls import path

from .views import (
    MesthiriAssignmentDetailView,
    MesthiriAssignmentListCreateView,
    MesthiriAssignmentOnDateView,
    MesthiriDetailView,
    MesthiriEntryDetailView,
    MesthiriListCreateView,
    MesthiriSiteEntryListCreateView,
)

urlpatterns = [
    path("", MesthiriListCreateView.as_view(), name="mesthiri-list-create"),
    path("<int:pk>/", MesthiriDetailView.as_view(), name="mesthiri-detail"),
    path("<int:mesthiri_id>/assignments/", MesthiriAssignmentListCreateView.as_view(), name="mesthiri-assignment-list-create"),
    path("assignments/<int:pk>/", MesthiriAssignmentDetailView.as_view(), name="mesthiri-assignment-detail"),
    path("<int:mesthiri_id>/assignment-on/", MesthiriAssignmentOnDateView.as_view(), name="mesthiri-assignment-on-date"),
    path("sites/<int:site_id>/entries/", MesthiriSiteEntryListCreateView.as_view(), name="mesthiri-site-entry-list-create"),
    path("entries/<int:pk>/", MesthiriEntryDetailView.as_view(), name="mesthiri-entry-detail"),
]
