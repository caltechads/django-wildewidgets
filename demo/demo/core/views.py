import inspect

from django.http import HttpResponseRedirect
from django.templatetags.static import static
from django.template.response import TemplateResponse
from django.views.generic import TemplateView
from django.urls import reverse, reverse_lazy

from chartjs.views.lines import BaseLineChartView

import pandas as pd
import altair as alt

from wildewidgets import (
    AltairChart,
    BarChart, 
    BreadrumbBlock,
    CodeWidget,
    DataTable,
    BasicMenu,
    DoughnutChart,
    HorizontalStackedBarChart, 
    HorizontalBarChart, 
    ListModelWidget,
    MenuMixin,
    PageHeader,
    PagedModelWidget,
    PieChart, 
    StackedBarChart, 
    StandardWidgetMixin,
    StringBlock,
    VerticalDarkMenu,
    WidgetListLayout,
)

from book_manager.models import Book, Author

from .wildewidgets import (
    ApexChart1Card,
    ApexHeader,
    ApexSparklineCard,
    AuthorListCard,
    AuthorListModelCardWidgetCard,
    BarChartCard,
    Block,
    BookModelTableCard,
    BusinessChartHeader,
    CollapseCard,
    CardCard,
    CodeCard,
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
    SciChart,
    SciChartCard,
    SciChartHeader,
    SciSyncChartCard,
    StringCard,
    TabCard,
    TableHeader, 
    TestChart, 
    TestDoughnutChart, 
    TestHistogram, 
    TestHorizontalHistogram, 
    TestTableCard,
)


class DemoMenu(VerticalDarkMenu):
    brand_image: str = static("core/images/dark_logo.png")
    brand_image_width: str = "100%"
    brand_text: str = "Wildewidgets Demo"
    brand_url: str = reverse_lazy("core:home")
    items = [
        (
            "Home", 
            "core:home"
        ),
        (
            'Tables', 
            'core:tables'
        ),
        (
            'Text Widgets',
            'core:text'
        ),
        (
            'List Widgets',
            'core:list'
        ),
        (
            'Structure Widgets',
            'core:structure'
        ),
        (
            'Modal Widgets',
            'core:modal'
        ),
        (
            'Charts', 
            [
                (
                    'Business Charts (ChartJS)', 
                    'core:charts'
                ), 
                (
                    'Scientific Charts (Altair)', 
                    'core:altair'
                ), 
                (
                    'Apex Charts', 
                    'core:apex'
                )
            ]
        ), 
    ]


class DemoBaseBreadcrumbs(BreadrumbBlock):
    title_class="fw-bold"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_breadcrumb('Django Wildewidgets Demo', reverse_lazy('core:home'))


class DemoStandardMixin(StandardWidgetMixin, MenuMixin):
    # template_name='core/standard.html'
    template_name='core/intermediate.html'
    menu_class = DemoMenu


class HomeView(DemoStandardMixin, TemplateView):
    menu_item = 'Home'

    def get_content(self):
        return HomeBlock()

    def get_breadcrumbs(self):
        breadcrumbs = DemoBaseBreadcrumbs()
        breadcrumbs.add_breadcrumb('Home')
        return breadcrumbs


class ChartView(DemoStandardMixin, TemplateView):
    menu_item = 'Charts'

    def get_content(self):
        layout = WidgetListLayout(f"Basic Business Charts w/ ChartJS", css_class='mt-4')
        layout.add_widget(PieCard(), "Pie Chart", "pie-chart")
        layout.add_widget(DonutCard(), "AJAX Donut Chart", "circle")
        layout.add_widget(BarChartCard(), "Bar Chart", "bar-chart")
        layout.add_widget(HorizontalBarChartCard(), "AJAX Horizontal Bar Chart", "bar-chart-steps")
        layout.add_widget(HistogramCard(), "Histogram", "bar-chart")
        layout.add_widget(HorizontalHistogramCard(), "AJAX Horizontal Histogram", "bar-chart-steps")
        return layout

    def get_breadcrumbs(self):
        breadcrumbs = DemoBaseBreadcrumbs()
        breadcrumbs.add_breadcrumb('Business Charts')
        return breadcrumbs


class AltairView(DemoStandardMixin, TemplateView):
    menu_item = 'Charts'

    def get_content(self):
        layout = WidgetListLayout(f"Scientific Charts w/ Altair", css_class='mt-4')    
        layout.add_widget(SciSyncChartCard(), "Altair Chart", "graph-up")
        layout.add_widget(SciChartCard(), "AJAX Altair Chart", "graph-down")
        return layout

    def get_breadcrumbs(self):
        breadcrumbs = DemoBaseBreadcrumbs()
        breadcrumbs.add_breadcrumb('Scientific Charts')
        return breadcrumbs


class ApexChartView(DemoStandardMixin, TemplateView):
    menu_item = 'Charts'

    def get_content(self):
        layout = WidgetListLayout(f"Apex Charts", css_class='mt-4')    
        layout.add_widget(ApexChart1Card(), "AJAX Apex Chart", "graph-up")
        layout.add_widget(ApexSparklineCard(), "Apex Sparkline Chart", "graph-down")
        return layout

    def get_breadcrumbs(self):
        breadcrumbs = DemoBaseBreadcrumbs()
        breadcrumbs.add_breadcrumb('Apex Charts')
        return breadcrumbs


class TableView(DemoStandardMixin, TemplateView):
    menu_item = 'Tables'

    def get_content(self):
        layout = WidgetListLayout(f"Tables", css_class='mt-4')    
        layout.add_widget(DataTableCard(), "Basic Static Table", "table")
        layout.add_widget(TestTableCard(), "AJAX Model Table", "table")
        layout.add_widget(BookModelTableCard(), "Basic Model Table", "table")
        return layout

    def get_breadcrumbs(self):
        breadcrumbs = DemoBaseBreadcrumbs()
        breadcrumbs.add_breadcrumb('Tables')
        return breadcrumbs


class TextWidgetView(DemoStandardMixin, TemplateView):
    menu_item = 'Text Widgets'

    def get_content(self):
        layout = WidgetListLayout(f"Text Widgets", css_class='mt-4')    
        layout.add_widget(MarkdownCard(), "Markdown Widget", "file-text")
        layout.add_widget(HTMLCard(), "HTML Widget", "file-code")
        layout.add_widget(CodeCard(), "Code Widget", "file-binary")
        layout.add_widget(StringCard())
        return layout

    def get_breadcrumbs(self):
        breadcrumbs = DemoBaseBreadcrumbs()
        breadcrumbs.add_breadcrumb('Text Widgets')
        return breadcrumbs


class ListWidgetView(DemoStandardMixin, TemplateView):
    menu_item = 'List Widgets'

    def get_content(self):
        layout = WidgetListLayout(f"List Widgets", css_class='mt-4')    
        layout.add_widget(PagedBookCard())
        layout.add_widget(AuthorListCard())
        layout.add_widget(AuthorListModelCardWidgetCard())
        return layout

    def get_breadcrumbs(self):
        breadcrumbs = DemoBaseBreadcrumbs()
        breadcrumbs.add_breadcrumb('List Widgets')
        return breadcrumbs


class StructureWidgetView(DemoStandardMixin, TemplateView):
    menu_item = 'Structure Widgets'

    def get_content(self):
        layout = WidgetListLayout(f"Structure Widgets", css_class='mt-4')    
        layout.add_widget(TabCard(), "Tab Widget", "folder")
        layout.add_widget(CardCard(), "Card Widget", "card-heading")
        layout.add_widget(CrispyFormCard(), "Crispy Form Widget", "ui-checks")
        layout.add_widget(CollapseCard(), "Collapse Widget", "arrows-collapse")
        layout.add_widget(HorizontalLayoutCard(), "Horizontal Layout Widget", "grid-3x2-gap")
        return layout

    def post(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('core:structure'))

    def get_breadcrumbs(self):
        breadcrumbs = DemoBaseBreadcrumbs()
        breadcrumbs.add_breadcrumb('Structure Widgets')
        return breadcrumbs
    

class ModalView(DemoStandardMixin, TemplateView):
    menu_item = 'Modal Widgets'

    def get_content(self):
        layout = WidgetListLayout(f"Modal Widget", css_class='mt-4')    
        layout.add_widget(ModalCard(), "Modal Widget", "window-fullscreen")
        layout.add_widget(CrispyFormModalCard(), "Crispy Form Modal Widget", "ui-checks")
        return layout

    def post(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('core:modal'))

    def get_breadcrumbs(self):
        breadcrumbs = DemoBaseBreadcrumbs()
        breadcrumbs.add_breadcrumb('Modal Widgets')
        return breadcrumbs
