from django.urls import include, path
from wildewidgets import WildewidgetDispatch

from .core import urls as core_urls

urlpatterns = [
    path("wildewidgets_json", WildewidgetDispatch.as_view(), name="wildewidgets_json"),
    path("", include(core_urls, namespace="core")),
]
