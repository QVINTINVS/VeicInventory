"""
URL configuration for inventory project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView

from wrf_standard.views import (
    WRFStandardEmissionListView,
    WRFStandardEmissionCreateView,
    WRFStandardEmissionUpdateView,
    WRFStandardEmissionDeleteView,
    WRFStandardVisualizeView,
    get_netcdf_data,
)



urlpatterns = [
    path("", RedirectView.as_view(pattern_name="wrf-standard", permanent=False)),

    path("admin/", admin.site.urls),
    path("wrf-standard/", WRFStandardEmissionListView.as_view(), name="wrf-standard"),
    path("wrf-standard/add/", WRFStandardEmissionCreateView.as_view(), name="wrf-standard_add"),
    path("wrf-standard/<int:pk>/edit/", WRFStandardEmissionUpdateView.as_view(), name="wrf-standard_edit"),
    path("wrf-standard/<int:pk>/delete/", WRFStandardEmissionDeleteView.as_view(), name="wrf-standard_delete"),
    
    path("wrf-standard/visualize/", WRFStandardVisualizeView.as_view(), name="wrf-standard_visualize"),
    path("get_netcdf_data/", get_netcdf_data, name="get_netcdf_data"),
]
