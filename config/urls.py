from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path(
        "admin/",
        admin.site.urls,
    ),

    path(
        "api/auth/",
        include("accounts.urls"),
    ),

    path(
        "api/sites/",
        include("sites.urls"),
    ),
    
    path(
        "api/labour/",
        include("labour.urls"),
    ),
    
    path(
        "api/mesthiri/",
        include("mesthiri.urls"),
    ),
    
    path(
        "api/materials/",
        include("materials.urls"),
    ),
    
    path(
        "api/reports/",
        include("common.urls"),
    ),
]