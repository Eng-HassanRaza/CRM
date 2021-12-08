# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path
from apps.crm import views

urlpatterns = [
    # The home page
    path('agent_client', views.agent_client, name='agent_client'),
    path('agent_client/add/', views.agent_client_add, name='agent_client_add'),
]