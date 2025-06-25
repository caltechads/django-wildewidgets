from django.urls import path

from .views import (
    AltairView,
    ApexChartView,
    ChartView,
    HomeView,
    ListWidgetView,
    ModalView,
    StructureWidgetView,
    TableView,
    TextWidgetView,
)

# These URLs are loaded by demo/urls.py.
app_name = "core"
urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("altair", AltairView.as_view(), name="altair"),
    path("tables", TableView.as_view(), name="tables"),
    path("apex", ApexChartView.as_view(), name="apex"),
    path("text", TextWidgetView.as_view(), name="text"),
    path("list", ListWidgetView.as_view(), name="list"),
    path("structure", StructureWidgetView.as_view(), name="structure"),
    path("modal", ModalView.as_view(), name="modal"),
    path("charts", ChartView.as_view(), name="charts"),
]
