from typing import ClassVar

from django.http import HttpResponseRedirect
from django.templatetags.static import static
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView
from wildewidgets import (
    BreadcrumbBlock,
    MenuMixin,
    StandardWidgetMixin,
    VerticalDarkMenu,
    WidgetListLayout,
)

from .wildewidgets import (
    ApexChart1Card,
    ApexSparklineCard,
    AuthorListCard,
    AuthorListModelCardWidgetCard,
    BarChartCard,
    BookModelTableCard,
    CardCard,
    CodeCard,
    CollapseCard,
    CrispyFormCard,
    CrispyFormModalCard,
    DataTableCard,
    DonutCard,
    HistogramCard,
    HomeBlock,
    HorizontalBarChartCard,
    HorizontalHistogramCard,
    HorizontalLayoutCard,
    HTMLCard,
    MarkdownCard,
    ModalCard,
    PagedBookCard,
    PieCard,
    SciChartCard,
    SciSyncChartCard,
    StaticTableCard,
    StringCard,
    TabCard,
    TestTableCard,
    WidgetCellTableCard,
)


class DemoMenu(VerticalDarkMenu):
    """
    Demo menu for the demo project.
    """

    #: The brand image of the menu.
    brand_image: str = static("core/images/dark_logo.png")
    #: The width of the brand image.
    brand_image_width: str = "100%"
    #: The text of the brand.
    brand_text: str = "Wildewidgets Demo"
    #: The URL to navigate to when the logo image is clicked
    brand_url: str = reverse_lazy("core:home")
    #: The items of the menu.
    items: ClassVar[list[tuple[str, str | list[tuple[str, str]]]]] = [  # type: ignore[assignment]
        ("Home", "core:home"),
        ("Tables", "core:tables"),
        ("Text Widgets", "core:text"),
        ("List Widgets", "core:list"),
        ("Structure Widgets", "core:structure"),
        ("Modal Widgets", "core:modal"),
        (
            "Charts",
            [
                ("Business Charts (ChartJS)", "core:charts"),
                ("Scientific Charts (Altair)", "core:altair"),
                ("Apex Charts", "core:apex"),
            ],
        ),
    ]


class DemoBaseBreadcrumbs(BreadcrumbBlock):
    """
    Demo base breadcrumbs for the demo project.
    """

    #: The class of the title.
    title_class = "fw-bold"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_breadcrumb("Django Wildewidgets Demo", reverse_lazy("core:home"))


class DemoStandardMixin(StandardWidgetMixin, MenuMixin):
    """
    Mixin for the demo project that provides a standard template and menu.
    """

    #: The template name of the mixin.
    template_name: str = "core/intermediate.html"
    #: The menu class of the mixin.
    menu_class: type[VerticalDarkMenu] = DemoMenu


class HomeView(DemoStandardMixin, TemplateView):  # type: ignore[misc]
    """
    The home page for the demo project.
    """

    #: The menu item of the view.
    menu_item = "Home"

    def get_content(self):
        return HomeBlock()

    def get_breadcrumbs(self):
        breadcrumbs = DemoBaseBreadcrumbs()
        breadcrumbs.add_breadcrumb("Home")
        return breadcrumbs


class ChartView(DemoStandardMixin, TemplateView):  # type: ignore[misc]
    """
    The ChartJS page for the demo project.
    """

    #: The menu item of the view.
    menu_item = "Charts"

    def get_content(self) -> WidgetListLayout:
        """
        Return the content for the ChartJS page.
        """
        layout = WidgetListLayout("Basic Business Charts w/ ChartJS", css_class="mt-4")
        layout.add_widget(PieCard(), "Pie Chart", "pie-chart")
        layout.add_widget(DonutCard(), "AJAX Donut Chart", "circle")
        layout.add_widget(BarChartCard(), "Bar Chart", "bar-chart")
        layout.add_widget(
            HorizontalBarChartCard(), "AJAX Horizontal Bar Chart", "bar-chart-steps"
        )
        layout.add_widget(HistogramCard(), "Histogram", "bar-chart")
        layout.add_widget(
            HorizontalHistogramCard(), "AJAX Horizontal Histogram", "bar-chart-steps"
        )
        return layout

    def get_breadcrumbs(self) -> DemoBaseBreadcrumbs:
        """
        Return the breadcrumbs for the charts page.
        """
        breadcrumbs = DemoBaseBreadcrumbs()
        breadcrumbs.add_breadcrumb("Business Charts")
        return breadcrumbs


class AltairView(DemoStandardMixin, TemplateView):  # type: ignore[misc]
    """
    The Altair scientific charts page.
    """

    #: The menu item of the view.
    menu_item = "Charts"

    def get_content(self):
        layout = WidgetListLayout("Scientific Charts w/ Altair", css_class="mt-4")
        layout.add_widget(SciSyncChartCard(), "Altair Chart", "graph-up")
        layout.add_widget(SciChartCard(), "AJAX Altair Chart", "graph-down")
        return layout

    def get_breadcrumbs(self):
        breadcrumbs = DemoBaseBreadcrumbs()
        breadcrumbs.add_breadcrumb("Scientific Charts")
        return breadcrumbs


class ApexChartView(DemoStandardMixin, TemplateView):  # type: ignore[misc]
    """
    The Apex charts page.
    """

    #: The menu item of the view.
    menu_item = "Charts"

    def get_content(self) -> WidgetListLayout:
        """
        Return the content for the Apex charts page.
        """
        layout = WidgetListLayout("Apex Charts", css_class="mt-4")
        layout.add_widget(ApexChart1Card(), "AJAX Apex Chart", "graph-up")
        layout.add_widget(ApexSparklineCard(), "Apex Sparkline Chart", "graph-down")
        return layout

    def get_breadcrumbs(self) -> DemoBaseBreadcrumbs:
        """
        Return the breadcrumbs for the Apex charts page.
        """
        breadcrumbs = DemoBaseBreadcrumbs()
        breadcrumbs.add_breadcrumb("Apex Charts")
        return breadcrumbs


class TableView(DemoStandardMixin, TemplateView):  # type: ignore[misc]
    """
    The tables page for the demo project.
    """

    #: The menu item of the view.
    menu_item = "Tables"

    def get_content(self) -> WidgetListLayout:
        """
        Return the content for the tables page.
        """
        layout = WidgetListLayout("Tables", css_class="mt-4")
        layout.add_widget(StaticTableCard(), "Static Table", "table")
        layout.add_widget(DataTableCard(), "Basic Static Table", "table")
        layout.add_widget(TestTableCard(), "AJAX Model Table", "table")
        layout.add_widget(BookModelTableCard(), "Basic Model Table", "table")
        layout.add_widget(WidgetCellTableCard(), "Widget Cell Table", "table")
        return layout

    def get_breadcrumbs(self) -> DemoBaseBreadcrumbs:
        """
        Return the breadcrumbs for the tables page.
        """
        breadcrumbs = DemoBaseBreadcrumbs()
        breadcrumbs.add_breadcrumb("Tables")
        return breadcrumbs


class TextWidgetView(DemoStandardMixin, TemplateView):  # type: ignore[misc]
    """
    The text widgets page for the demo project.
    """

    #: The menu item of the view.
    menu_item = "Text Widgets"

    def get_content(self) -> WidgetListLayout:
        """
        Return the content for the text widgets page.
        """
        layout = WidgetListLayout("Text Widgets", css_class="mt-4")
        layout.add_widget(MarkdownCard(), "Markdown Widget", "file-text")
        layout.add_widget(HTMLCard(), "HTML Widget", "file-code")
        layout.add_widget(CodeCard(), "Code Widget", "file-binary")
        layout.add_widget(StringCard())
        return layout

    def get_breadcrumbs(self) -> DemoBaseBreadcrumbs:
        """
        Return the breadcrumbs for the text widgets page.
        """
        breadcrumbs = DemoBaseBreadcrumbs()
        breadcrumbs.add_breadcrumb("Text Widgets")
        return breadcrumbs


class ListWidgetView(DemoStandardMixin, TemplateView):  # type: ignore[misc]
    """
    The list widgets page for the demo project.
    """

    #: The menu item of the view.
    menu_item = "List Widgets"

    def get_content(self) -> WidgetListLayout:
        """
        Return the content for the list widgets page.
        """
        layout = WidgetListLayout("List Widgets", css_class="mt-4")
        layout.add_widget(PagedBookCard())
        layout.add_widget(AuthorListCard())
        layout.add_widget(AuthorListModelCardWidgetCard())
        return layout

    def get_breadcrumbs(self) -> DemoBaseBreadcrumbs:
        """
        Return the breadcrumbs for the list widgets page.
        """
        breadcrumbs = DemoBaseBreadcrumbs()
        breadcrumbs.add_breadcrumb("List Widgets")
        return breadcrumbs


class StructureWidgetView(DemoStandardMixin, TemplateView):  # type: ignore[misc]
    """
    The structure widgets page for the demo project.
    """

    #: The menu item of the view.
    menu_item = "Structure Widgets"

    def get_content(self) -> WidgetListLayout:
        """
        Return the content for the structure widgets page.
        """
        layout = WidgetListLayout("Structure Widgets", css_class="mt-4")
        layout.add_widget(TabCard(), "Tab Widget", "folder")
        layout.add_widget(CardCard(), "Card Widget", "card-heading")
        layout.add_widget(CrispyFormCard(), "Crispy Form Widget", "ui-checks")
        layout.add_widget(CollapseCard(), "Collapse Widget", "arrows-collapse")
        layout.add_widget(
            HorizontalLayoutCard(), "Horizontal Layout Widget", "grid-3x2-gap"
        )
        return layout

    def post(self, request, *args, **kwargs):  # noqa: ARG002
        """
        Redirect to the structure widgets page.
        """
        return HttpResponseRedirect(reverse("core:structure"))

    def get_breadcrumbs(self) -> DemoBaseBreadcrumbs:
        """
        Return the breadcrumbs for the structure widgets page.
        """
        breadcrumbs = DemoBaseBreadcrumbs()
        breadcrumbs.add_breadcrumb("Structure Widgets")
        return breadcrumbs


class ModalView(DemoStandardMixin, TemplateView):  # type: ignore[misc]
    """
    The modal widgets page for the demo project.
    """

    #: The menu item of the view.
    menu_item = "Modal Widgets"

    def get_content(self):
        layout = WidgetListLayout("Modal Widget", css_class="mt-4")
        layout.add_widget(ModalCard(), "Modal Widget", "window-fullscreen")
        layout.add_widget(
            CrispyFormModalCard(), "Crispy Form Modal Widget", "ui-checks"
        )
        return layout

    def post(self, request, *args, **kwargs):  # noqa: ARG002
        return HttpResponseRedirect(reverse("core:modal"))

    def get_breadcrumbs(self):
        breadcrumbs = DemoBaseBreadcrumbs()
        breadcrumbs.add_breadcrumb("Modal Widgets")
        return breadcrumbs
