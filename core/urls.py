# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib import admin
from django.urls import path, include  # add this

urlpatterns = [
    path('admin/', admin.site.urls),
    path("crm/", include("apps.crm.urls")),
    path('', include('social_django.urls', namespace='social')),
    path("", include("apps.authentication.urls")),
    path("", include("apps.home.urls")),
]
