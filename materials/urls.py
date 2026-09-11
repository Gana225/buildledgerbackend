from django.urls import path

from .views import (
    MaterialListCreateView,
    MaterialDetailView,
)


urlpatterns = [

    path(
        "sites/<int:site_id>/",
        MaterialListCreateView.as_view(),
        name="material-list-create",
    ),

    path(
        "<int:pk>/",
        MaterialDetailView.as_view(),
        name="material-detail",
    ),
]