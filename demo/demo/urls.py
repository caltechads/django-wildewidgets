"""demo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from django.urls import path, include
from django.conf import settings

from wildewidgets import WildewidgetDispatch

from .core import urls as core_urls


urlpatterns = [
    # This setup assumes that you're making an access.caltech app, which needs the app name as a prefix for all URLs.
    # If that's not true, you can change this to whatever base path you want, including ''.
    path('wildewidgets_json', WildewidgetDispatch.as_view(), name='wildewidgets_json'),
    path('', include(core_urls, namespace='core')),
]
