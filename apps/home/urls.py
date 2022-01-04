# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path
from apps.home import views
from apps.crm.views import agent_client
urlpatterns = [

    # The home page
    path('', agent_client, name='home'),
    path('settings', views.settings, name='settings'),

    # Matches any html file
    re_path(r'^.*\.*', views.pages, name='pages'),

]
