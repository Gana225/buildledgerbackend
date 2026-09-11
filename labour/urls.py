# from django.urls import path

# from .views import (
#     LabourListCreateView,
#     LabourDetailView,
#     LabourEntryListCreateView,
#     LabourEntryDetailView,
# )


# urlpatterns = [

#     path(
#         "sites/<int:site_id>/",
#         LabourListCreateView.as_view(),
#         name="labour-list-create",
#     ),

#     path(
#         "<int:pk>/",
#         LabourDetailView.as_view(),
#         name="labour-detail",
#     ),

#     path(
#         "sites/<int:site_id>/entries/",
#         LabourEntryListCreateView.as_view(),
#         name="labour-entry-list-create",
#     ),

#     path(
#         "entries/<int:pk>/",
#         LabourEntryDetailView.as_view(),
#         name="labour-entry-detail",
#     ),
# ]


from django.urls import path

from .views import (
    LabourListCreateView,
    LabourDetailView,
    LabourAssignmentListCreateView,
    LabourAssignmentDetailView,
    LabourAssignmentOnDateView,
    LabourSiteEntryListCreateView,
    LabourEntryDetailView,
)


urlpatterns = [

    # ----------------------------------------
    # Labour master
    # ----------------------------------------

    path(
        "",
        LabourListCreateView.as_view(),
        name="labour-list-create",
    ),

    path(
        "<int:pk>/",
        LabourDetailView.as_view(),
        name="labour-detail",
    ),

    # ----------------------------------------
    # Assignment history
    # ----------------------------------------

    path(
        "<int:labour_id>/assignments/",
        LabourAssignmentListCreateView.as_view(),
        name="labour-assignment-list-create",
    ),

    path(
        "assignments/<int:pk>/",
        LabourAssignmentDetailView.as_view(),
        name="labour-assignment-detail",
    ),

    path(
        "<int:labour_id>/assignment-on/",
        LabourAssignmentOnDateView.as_view(),
        name="labour-assignment-on-date",
    ),

    # ----------------------------------------
    # Site accounting entries
    # ----------------------------------------

    path(
        "sites/<int:site_id>/entries/",
        LabourSiteEntryListCreateView.as_view(),
        name="labour-site-entry-list-create",
    ),

    path(
        "entries/<int:pk>/",
        LabourEntryDetailView.as_view(),
        name="labour-entry-detail",
    ),
]