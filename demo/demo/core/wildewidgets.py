from __future__ import annotations

import inspect
import random
from typing import TYPE_CHECKING, ClassVar, Literal

import altair as alt
import pandas as pd
from book_manager.forms import MinimalBookForm
from book_manager.models import Author, Book
from wildewidgets import (
    AltairChart,
    ApexChartBase,
    ApexDatasetBase,
    ApexJSONMixin,
    ApexSparkline,
    BasicHeader,
    BasicModelTable,
    Block,
    CardHeader,
    CardWidget,
    CodeWidget,
    CollapseWidget,
    CrispyFormModalWidget,
    CrispyFormWidget,
    DataTable,
    DataTableFilter,
    DoughnutChart,
    FontIcon,
    Histogram,
    HorizontalHistogram,
    HorizontalLayoutBlock,
    HorizontalStackedBarChart,
    HTMLWidget,
    LabelBlock,
    LinkButton,
    ListModelCardWidget,
    ListModelWidget,
    MarkdownWidget,
    ModalButton,
    ModalWidget,
    PagedModelWidget,
    PageHeader,
    PieChart,
    StackedBarChart,
    StaticTableWidget,
    TabbedWidget,
    TablerFontIcon,
    TagBlock,
    TimeStamp,
    UnorderedList,
    Widget,
    WidgetCellMixin,
    WidgetStream,
)

from .models import Measurement

if TYPE_CHECKING:
    from django.db.models import Model, QuerySet


def get_code_block(fn):
    """
    The lines are part of a function, so we need to remove the
    first line, which contains the function name, and the last
    line, which is just the return, and we need to remove any
    indentation on the remaining lines.

    Args:
        fn: the function to inspect

    """
    lines = inspect.getsourcelines(fn)[0]
    code = ""
    if len(lines) < 2:  # noqa: PLR2004
        return None
    space_len = len(lines[1]) - len(lines[1].strip())
    for line in lines[1:-1]:
        code += line[space_len - 1 :]
    return code


class BusinessChartHeader(BasicHeader):
    """
    Basic business charts with ChartJS.
    """

    header_level = 5
    header_type = "display"
    header_text = "Basic Business Charts w/ ChartJS"


class TestChart(StackedBarChart):
    """
    Test chart with ChartJS.
    """

    def get_categories(self) -> list[str]:
        """
        Return 7 labels for the x-axis.

        Returns:
            A list of 7 labels for the x-axis.

        """
        return ["January", "February", "March", "April", "May", "June", "July"]

    def get_dataset_labels(self) -> list[str]:
        """
        Return names of datasets.

        Returns:
            A list of names of datasets.

        """
        return [
            "Central",
            "Eastside",
            "Westside",
            "Central2",
            "Eastside2",
            "Westside2",
            "Central3",
            "Eastside3",
            "Westside3",
        ]

    def get_datasets(self) -> list[list[float]]:
        """Return 3 datasets to plot."""
        return [
            [750, 440, 920, 1100, 440, 950, 350],
            [410, 1920, 180, 300, 730, 870, 920],
            [870, 210, 940, 3000, 900, 130, 650],
            [750, 440, 920, 1100, 440, 950, 350],
            [410, 920, 180, 2000, 730, 870, 920],
            [870, 210, 940, 300, 900, 130, 650],
            [750, 440, 920, 1100, 440, 950, 3500],
            [410, 920, 180, 3000, 730, 870, 920],
            [870, 210, 940, 300, 900, 130, 650],
        ]


class TestDoughnutChart(DoughnutChart):
    """
    Test doughnut chart with ChartJS.
    """

    #: Whether to show the legend.
    legend = True
    #: The position of the legend.
    legend_position = "right"
    #: Whether to color the chart.
    color = False

    def get_categories(self) -> list[str]:
        """
        Return names of categories.

        Returns:
            A list of names of categories.

        """
        return ["January", "February", "March", "April", "May", "June", "July"]

    def get_dataset(self) -> list[int]:
        """
        Return a dataset.

        Returns:
            A list of values for the dataset.

        """
        return [75, 44, 92, 11, 44, 95, 53]


class TestHistogram(Histogram):
    """
    Test histogram with ChartJS.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        mu = 0
        sigma = 50
        nums = []
        bin_count = 40
        for _ in range(10000):
            temp = random.gauss(mu, sigma)
            nums.append(temp)

        self.build(nums, bin_count)


class TestHorizontalHistogram(HorizontalHistogram):
    """
    Test horizontal histogram with ChartJS.
    """

    #: Whether to color the chart.
    color = False

    def load(self) -> None:
        """
        Load the histogram data.

        """
        mu = 100
        sigma = 30
        nums = []
        bin_count = 50
        for _ in range(10000):
            temp = random.gauss(mu, sigma)
            nums.append(temp)

        self.build(nums, bin_count)


class SciChartHeader(BasicHeader):
    """
    Header for the scientific charts with Altair page.
    """

    #: The level of the header.
    header_level = 5
    #: The type of the header.
    header_type = "display"
    #: The text of the header.
    header_text = "Scientific Charts w/ Altair"


class SciChart(AltairChart):
    """
    Scientific chart with Altair.
    """

    #: The title of the chart.
    title = "Scientific Proofiness"

    def load(self) -> None:
        """
        Load the chart data.

        """
        data = pd.DataFrame({"a": list("CCCDDDEEE"), "b": [2, 7, 4, 1, 2, 6, 8, 4, 10]})
        spec = alt.Chart(data).mark_point().encode(x="a", y="b")
        self.set_data(spec)


class WidgetCodeTab(TabbedWidget):
    """
    Tabbed widget for the code behind the widget displayed in the tab.
    """

    def __init__(self, *args, **kwargs) -> None:
        title = kwargs.pop("title", "")
        code = kwargs.pop("code", [])
        widget = kwargs.pop("widget", None)
        super().__init__(*args, **kwargs)
        if not isinstance(code, list):
            code = [code]
        code_stream = WidgetStream()
        for code_block in code:
            code_widget = CodeWidget(code=code_block, language="python")
            code_stream.add_widget(code_widget)
        self.add_tab(f"{title} Widget", widget)
        self.add_tab(f"{title} Code", code_stream)


class SciSyncChartCard(CardWidget):
    """
    Scientific chart with Altair.
    """

    #: The title of the card.
    title: str = "Scientific Chart"
    #: The subtitle of the card.
    subtitle: str = "Altair"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(SciSyncChartCard.get_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_widget())
        self.set_widget(tab, "mb-5")

    def get_widget(self) -> AltairChart:
        """
        Return the scientific chart.

        Returns:
            The scientific chart.

        """
        data = pd.DataFrame({"a": list("CCCDDDEEE"), "b": [2, 7, 4, 1, 2, 6, 8, 4, 7]})
        spec = alt.Chart(data).mark_point().encode(x="a", y="b")
        chart = AltairChart(title=self.title)
        chart.set_data(spec)
        return chart


class SciChartCard(CardWidget):
    """
    Scientific chart with Altair (AJAX).
    """

    #: The title of the card.
    title: str = "Scientific Chart"
    #: The subtitle of the card.
    subtitle = "Altair (AJAX)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        chart = SciChart()
        code = inspect.getsource(SciChart)
        tab = WidgetCodeTab(code=code, widget=chart)
        self.set_widget(tab, "mb-5")


class TestTable(DataTable):
    """
    Test table with DatatablesJS.
    """

    #: The model to use for the table.
    model = Measurement
    #: The ID of the table.
    table_id: str = "data_measurement"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add all the columns.
        self.add_column("name")
        self.add_column("time", searchable=False)
        self.add_column("pressure", align="right")
        self.add_column("temperature", align="right")
        self.add_column("restricted", visible=False)
        self.add_column("open", sortable=False)

        # Set the `restricted` filter.
        filtr = DataTableFilter()
        filtr.add_choice("True", "True")
        filtr.add_choice("False", "False")
        self.add_filter("restricted", filtr)

        # Set the `open` filter.
        filtr = DataTableFilter()
        filtr.add_choice("True", "True")
        filtr.add_choice("False", "False")
        self.add_filter("open", filtr)

        # Set the `pressure` filter.
        filtr = DataTableFilter()
        filtr.add_choice("< 1000", "level_1000")
        filtr.add_choice("1000-2000", "level_2000")
        filtr.add_choice("2000-3000", "level_3000")
        self.add_filter("pressure", filtr)

    def filter_pressure_column(self, qs, column, value) -> QuerySet:  # noqa: ARG002
        """
        Filter endpoint for the ``pressure`` column.

        Args:
            qs: The queryset to filter.
            column: The column to filter (unused).
            value (str): The value to filter by.

        Returns:
            The filtered queryset.

        """
        if value == "level_1000":
            qs = qs.filter(pressure__lt=1000)
        elif value == "level_2000":
            qs = qs.filter(pressure__lt=2000).filter(pressure__gte=1000)
        elif value == "level_3000":
            qs = qs.filter(pressure__lt=3000).filter(pressure__gte=2000)
        else:
            qs = qs.filter(pressure__contains=value)
        return qs

    def filter_restricted_column(self, qs, column, value) -> QuerySet:  # noqa: ARG002
        """
        Filter endpoint for the ``restricted`` column.

        Args:
            qs: The queryset to filter.
            column: The column to filter (unused).
            value: The value to filter by.

        Returns:
            The filtered queryset.

        """
        test = value == "True"
        return qs.filter(restricted=test)

    def filter_open_column(self, qs, column, value) -> QuerySet:  # noqa: ARG002
        """
        Filter endpoint for the ``open`` column.

        Args:
            qs: The queryset to filter.
            column: The column to filter (unused).
            value (str): The value to filter by.

        Returns:
            The filtered queryset.

        """
        test = value == "True"
        return qs.filter(open=test)


class PieCard(CardWidget):
    """
    Pie chart with ChartJS.
    """

    #: The title of the card.
    title: str = "Pie Chart"
    #: The subtitle of the card.
    subtitle: str = "ChartJS"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(PieCard.get_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_widget())
        self.set_widget(tab, "mb-5")

    def get_widget(self) -> PieChart:
        """
        Return the pie chart.

        Returns:
            The pie chart.

        """
        pie = PieChart(title="Dramatic Colors")
        pie.set_categories(
            ["January", "February", "March", "April", "May", "June", "July"]
        )
        pie.add_dataset([75, 44, 92, 11, 44, 95, 35])
        return pie


class DonutCard(CardWidget):
    """
    Donut chart with ChartJS (AJAX).
    """

    #: The title of the card.
    title: str = "Donut Chart"
    #: The subtitle of the card.
    subtitle: str = "ChartJS (AJAX)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        donut = TestDoughnutChart()
        code = inspect.getsource(TestDoughnutChart)
        tab = WidgetCodeTab(code=code, widget=donut)
        self.set_widget(tab, "mb-5")


class BarChartCard(CardWidget):
    """
    Bar chart with ChartJS (AJAX).
    """

    #: The title of the card.
    title: str = "Bar Chart"
    #: The subtitle of the card.
    subtitle: str = "ChartJS (AJAX)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        chart = TestChart(width="500", height="400", thousands=True)
        code = inspect.getsource(TestChart)
        tab = WidgetCodeTab(code=code, widget=chart)
        self.set_widget(tab, "mb-5")


class HorizontalBarChartCard(CardWidget):
    """
    Horizontal bar chart with ChartJS.
    """

    #: The title of the card.
    title: str = "Horizontal Bar Chart"
    #: The subtitle of the card.
    subtitle: str = "ChartJS"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        code = get_code_block(HorizontalBarChartCard.get_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_widget())
        self.set_widget(tab, "mb-5")

    def get_widget(self) -> HorizontalStackedBarChart:
        """
        Return the horizontal bar chart.

        Returns:
            The horizontal bar chart.

        """
        barchart = HorizontalStackedBarChart(
            title="Formage Through July",
            money=True,
            legend=True,
            width="500",
            color=False,
        )
        barchart.set_categories(
            ["January", "February", "March", "April", "May", "June", "July"]
        )
        barchart.add_dataset([75, 44, 92, 11, 44, 95, 35], "Central")
        barchart.add_dataset([41, 92, 18, 35, 73, 87, 92], "Eastside")
        barchart.add_dataset([87, 21, 94, 13, 90, 13, 65], "Westside")
        return barchart


class HistogramCard(CardWidget):
    """
    Histogram with ChartJS (AJAX).
    """

    #: The title of the card.
    title: str = "Histogram"
    #: The subtitle of the card.
    subtitle: str = "ChartJS (AJAX)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        histogram = TestHistogram(width="500", height="400")
        code = inspect.getsource(TestHistogram)
        tab = WidgetCodeTab(code=code, widget=histogram)
        self.set_widget(tab, "mb-5")


class HorizontalHistogramCard(CardWidget):
    """
    Horizontal histogram with ChartJS.
    """

    #: The title of the card.
    title: str = "Horizontal Histogram"
    #: The subtitle of the card.
    subtitle: str = "ChartJS"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        histogram = TestHorizontalHistogram(width="500", height="400")
        code = inspect.getsource(TestHorizontalHistogram)
        tab = WidgetCodeTab(code=code, widget=histogram)
        self.set_widget(tab, "mb-5")


class TableHeader(BasicHeader):
    """
    Header for the scientific tables with DatatablesJS page.
    """

    #: The level of the header.
    header_level = 5
    #: The type of the header.
    header_type = "display"
    #: The text of the header.
    header_text = "Scientific Tables w/ DatatablesJS"
    #: The CSS class of the header.
    css_class = ""


class StaticTable(StaticTableWidget):
    """
    Static data table build with :class:`~wildewidgets.StaticTableWidget`.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_heading("Time")
        self.add_heading("Pressure")
        self.add_heading("Temperature")
        self.add_row([12, 53, 25])
        self.add_row([13, 63, 24])
        self.add_row([14, 73, 23])


class StaticTableCard(CardWidget):
    """
    Wrapper around the :class:`~demo.core.wildewidgets.StaticTable` widget.
    """

    #: The introduction text.
    INTRO: str = """
This table is built with :class:`~wildewidgets.StaticTableWidget`.
It is a static table that does not use dataTables.js useful for small lists of data,
especially data that is not in Django models.
"""

    #: The title of the card.
    title: str = "Static Table"
    #: The subtitle of the card.
    subtitle: str = "Static Table"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = inspect.getsource(StaticTable)
        text = Block(self.INTRO, css_class="mb-4")
        tab = WidgetCodeTab(code=code, widget=StaticTable())
        self.set_widget(Block(text, tab), "mb-5")


class DataTableCard(CardWidget):
    """
    Static Data table with DatatablesJS (Non-AJAX).
    """

    #: The title of the card.
    title: str = "Data Table"
    #: The subtitle of the card.
    subtitle: str = "DatatablesJS (Non-AJAX)"

    #: The introduction text.
    INTRO: str = """
This table is built on a lower level class that provides a lot of flexibility,
but can often require more code to specify.  You can use any data source as
appropriate. Here, we are manually adding data in rows.
"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(DataTableCard.get_widget)
        text = Block(self.INTRO, css_class="mb-4")
        tab = WidgetCodeTab(code=code, widget=self.get_widget())
        self.set_widget(Block(text, tab), "mb-5")

    def get_widget(self) -> DataTable:
        """
        Return the data table.

        Returns:
            The data table.

        """
        table = DataTable()
        table.is_data_list = False
        table.add_column("time")
        table.add_column("pressure")
        table.add_column("temperature")
        table.add_row(time=12, pressure=53, temperature=25)
        table.add_row(time=13, pressure=63, temperature=24)
        table.add_row(time=14, pressure=73, temperature=23)
        return table


class TestTableCard(CardWidget):
    """
    Wrapper around the :class:`~demo.core.wildewidgets.TestTable` widget.
    """

    #: The title of the card.
    title: str = "Test Table"
    #: The subtitle of the card.
    subtitle: str = "DatatablesJS (AJAX)"
    #: The introduction text.
    INTRO: str = """
This table is built on a lower level class that provides a lot of flexibility,
but can often require more code to specify. You can use any data source as
appropriate. Here, we are using a Django Model.
"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = inspect.getsource(TestTable)
        text = Block(self.INTRO, css_class="mb-4")
        tab = WidgetCodeTab(code=code, widget=TestTable())
        self.set_widget(Block(text, tab), "mb-5")


class BookModelTable(BasicModelTable):
    """
    Book model table with DatatablesJS (AJAX).
    """

    #: The model to use for the table.
    model: type[Model] = Book
    #: The fields to display in the table.
    fields: list[str] = ["title", "authors__full_name", "isbn"]  # noqa: RUF012
    #: The alignment of the columns.
    alignment: ClassVar[dict[str, Literal["left", "right", "center"]]] = {  # type: ignore[misc]
        "authors": "left",
    }
    #: The verbose names of the columns.
    verbose_names: dict[str, str] = {"authors__full_name": "Authors"}  # noqa: RUF012
    #: Whether to show the dataTables.js buttons
    buttons: bool = True
    #: Whether to stripe the table rows.
    striped: bool = True

    def render_authors__full_name_column(self, row, column):  # noqa: ARG002
        """
        Return the full name of the authors, split into multiple lines if there
        are multiple authors.

        Args:
            row: The row to render.
            column: The column to render.

        Returns:
            The full name of the authors.

        """
        authors = row.authors.all()
        if authors.count() > 1:
            return f"{authors[0].full_name} ... "
        return authors[0].full_name


class BookModelTableCard(CardWidget):
    """
    Wrapper around the :class:`~demo.core.wildewidgets.BookModelTable` widget.
    """

    #: The introduction text.
    INTRO: str = """
This table is built on a high level class designed to work easily with Django
models. It automatically generates the table columns and provides a lot of
flexibility for customization.  It is dynamic, using AJAX to retrieve data from
the server.
"""
    title = "Book Model Table"
    subtitle = "DatatablesJS (AJAX)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = inspect.getsource(BookModelTable)
        text = Block(self.INTRO, css_class="mb-4")
        tab = WidgetCodeTab(code=code, widget=BookModelTable())
        self.set_widget(Block(text, tab), "mb-5")


class PressureCellWidget(Block):
    """
    Pressure cell widget with FontIcon.  This is used to demonstrate the use of
    cell widgets in a table.
    """

    def __init__(self, *args, row=None, column="", **kwargs):  # noqa: ARG002
        value = row.pressure
        if value > 2000:  # noqa: PLR2004
            icon = "thermometer-high"
            color = "red"
        elif value > 1000:  # noqa: PLR2004
            icon = "thermometer-half"
            color = "orange"
        else:
            icon = "thermometer-low"
            color = "green"
        super().__init__(
            HorizontalLayoutBlock(
                FontIcon(icon=icon, color=color), f"{value}", justify="end"
            ),
            *args,
            **kwargs,
        )


class WidgetCellTable(WidgetCellMixin, BasicModelTable):  # type: ignore[misc]
    """
    Table with widget cells.  This is used to demonstrate the use of widget cells
    in a table.
    """

    #: The fields to display in the table.
    fields: list[str] = ["name", "pressure", "temperature"]  # noqa: RUF012
    #: The cell widgets to use for the table.
    cell_widgets: dict[str, type[Widget]] = {"pressure": PressureCellWidget}  # noqa: RUF012
    #: The model to use for the table.
    model: type[Model] = Measurement
    #: The alignment of the columns.
    alignment: ClassVar[dict[str, Literal["left", "right", "center"]]] = {  # type: ignore[misc]
        "pressure": "right",
        "temperature": "right",
    }
    #: Whether to stripe the table rows.
    striped: bool = True


class WidgetCellTableCard(CardWidget):
    """
    Wrapper around the :class:`~demo.core.wildewidgets.WidgetCellTable` widget.
    """

    #: The title of the card.
    title: str = "Widget Cell Table"
    #: The subtitle of the card.
    subtitle: str = "DatatablesJS (AJAX)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = []
        code.append(inspect.getsource(PressureCellWidget))
        code.append(inspect.getsource(WidgetCellTable))
        tab = WidgetCodeTab(code=code, widget=WidgetCellTable())
        self.set_widget(tab, "mb-5")


class ApexHeader(BasicHeader):
    """
    Header for the Apex Charts page.
    """

    #: The level of the header.
    header_level = 5
    #: The type of the header.
    header_type = "display"
    #: The text of the header.
    header_text = "Apex Charts"
    #: The CSS class of the header.
    css_class = ""


class ApexLineDataset(ApexDatasetBase):
    """
    Apex line dataset.
    """

    #: The name of the dataset.
    name: str = "Data"

    def __init__(self, *args, **kwargs):  # noqa: ARG002
        super().__init__(**kwargs)
        self.data = [25, 66, 41, 89, 63, 25, 44, 12, 36, 9, 54]


class ApexLineChart(ApexJSONMixin, ApexChartBase):
    """
    Apex line chart.
    """

    #: The type of the chart.
    chart_type: str = "line"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_categories(
            [
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ]
        )

    def load(self) -> None:
        """
        Load the Apex line dataset.
        """
        self.add_dataset(ApexLineDataset())


class ApexChart1Card(CardWidget):
    """
    Wrapper around the :class:`~demo.core.wildewidgets.ApexLineChart` widget.
    """

    #: The title of the card.
    title: str = "Apex Charts"
    #: The subtitle of the card.
    subtitle: str = "Line Chart (AJAX)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = []
        code.append(inspect.getsource(ApexLineDataset))
        code.append(inspect.getsource(ApexLineChart))
        tab = WidgetCodeTab(code=code, widget=ApexLineChart())
        self.set_widget(tab, "mb-5")


class ApexSparkLineChart(ApexSparkline):
    """
    Apex spark line chart.
    """

    #: The type of the chart.
    chart_type: str = "bar"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_dataset(ApexLineDataset())
        self.add_categories(
            [
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ]
        )


class ApexSparklineCard(CardWidget):
    """
    Wrapper around the :class:`~demo.core.wildewidgets.ApexSparkLineChart` widget.
    """

    #: The title of the card.
    title: str = "Apex Charts"
    #: The subtitle of the card.
    subtitle: str = "Sparkline"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = []
        code.append(inspect.getsource(ApexLineDataset))
        code.append(inspect.getsource(ApexSparkLineChart))
        tab = WidgetCodeTab(code=code, widget=ApexSparkLineChart())
        self.set_widget(tab, "mb-5")


class MarkdownCard(CardWidget):
    """
    Demonstration of the :class:`~wildewidgets.MarkdownWidget` widget.
    """

    #: The markdown text.
    MARKDOWN: str = """
# Markdown Example

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu
fugiat nulla pariatur.

    Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia
    deserunt mollit anim id est laborum.

## de Finibus Bonorum et Malorum

1. Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium
   doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore
   veritatis et quasi architecto beatae vitae dicta sunt explicabo.

2. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit,
   sed quia...
"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(MarkdownCard.get_markdown_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_markdown_widget())
        self.set_widget(tab, "mb-5")

    def get_markdown_widget(self) -> MarkdownWidget:
        """
        Return the Markdown widget.
        """
        return MarkdownWidget(text=self.MARKDOWN)


class HTMLCard(CardWidget):
    """
    Demonstration of the :class:`~wildewidgets.HTMLWidget` widget.
    """

    #: The HTML text.
    HTML: str = """
<h1>HTML Example</h1>
<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod
tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam,
quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo
consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum
dolore eu fugiat nulla pariatur. </p>

<pre><code>Excepteur sint occaecat cupidatat non proident, sunt in culpa qui
officia deserunt mollit anim id est laborum.  </code></pre>

<h2>de Finibus Bonorum et Malorum</h2>
<ol>
<li>
<p>Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium
doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore
veritatis et quasi architecto beatae vitae dicta sunt explicabo.</p>
</li>
<li>
<p>Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit,
sed quia...</p>
</li>
</ol>
"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(HTMLCard.get_html_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_html_widget())
        self.set_widget(tab, "mb-5")

    def get_html_widget(self) -> HTMLWidget:
        """
        Return the HTML widget.
        """
        return HTMLWidget(html=self.HTML)


class CodeCard(CardWidget):
    """
    Demonstration of the :class:`~wildewidgets.CodeWidget` widget.
    """

    #: The title of the card.
    title: str = "Code"
    #: The subtitle of the card.
    subtitle: str = "Code Widget"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(CodeCard.get_code_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_code_widget())
        self.set_widget(tab, "mb-5")

    def get_code_widget(self) -> CodeWidget:
        """
        Return the Code widget.
        """
        return CodeWidget(code=inspect.getsource(MarkdownCard), language="python")


class StringCard(CardWidget):
    """
    Demonstration of these widgets:

    - :class:`~wildewidgets.StringBlock`
    - :class:`~wildewidgets.TimeStampBlock`
    - :class:`~wildewidgets.LabelBlock`
    - :class:`~wildewidgets.TagBlock`
    """

    #: The title of the card.
    title: str = "Various String Blocks"
    #: The icon of the card.
    icon: str = "fonts"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(StringCard.get_string_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_string_widget())
        self.set_widget(tab, "mb-5")

    def get_string_widget(self) -> Block:
        """
        Return the String widget.
        """
        return Block(
            Block("This is a string block", css_class="mb-2"),
            TimeStamp("4:53 PM - this is a time block."),
            Block(LabelBlock("This is a label block", css_class="my-2")),
            TagBlock("This is a tag block"),
        )


class BookModelWidget(Block):
    """
    Simple demonstration of using a :class:`~wildewidgets.Block` to
    display rows in a :class:`~wildewidgets.PagedModelWidget`.
    """

    #: The object to display.
    object: Model | None = None

    def __init__(self, object: Model | None = None, **kwargs) -> None:  # noqa: A002
        if object is None:
            msg = "object must be provided"
            raise ValueError(msg)
        authors = ", ".join([x.full_name for x in object.authors.all()])
        super().__init__(
            Block(
                f"{object.title} - {authors}", css_class="p-3 mb-1 border text-bg-light"
            ),
            **kwargs,
        )


class PagedBookWidget(PagedModelWidget):
    """
    Paged demonstration of using a :class:`~wildewidgets.PagedModelWidget` to
    display a list of objects.
    """

    #: The model to use for the widget.
    model = Book
    #: The widget to use for each object.
    model_widget = BookModelWidget
    #: The number of objects to display per page.
    paginate_by: int = 5


class PagedBookCard(CardWidget):
    """
    Wrapper around the :class:`~demo.core.wildewidgets.PagedBookWidget` widget.
    """

    #: The title of the card.
    title: str = "Paged Model Widget"
    #: The icon of the card.
    icon: str = "book"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = []
        code.append(inspect.getsource(BookModelWidget))
        code.append(inspect.getsource(PagedBookWidget))
        tab = WidgetCodeTab(code=code, widget=self.get_paged_book_widget())
        self.set_widget(tab, "mb-5")

    def get_paged_book_widget(self) -> PagedBookWidget:
        return PagedBookWidget()


class AuthorListCard(CardWidget):
    """
    Wrapper around the :class:`~demo.core.wildewidgets.AuthorListModelWidget` widget.
    """

    #: The title of the card.
    title: str = "List Model Widget"
    #: The icon of the card.
    icon: str = "people"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(AuthorListCard.get_author_list_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_author_list_widget())
        self.set_widget(tab, "mb-5")

    def get_author_list_widget(self) -> ListModelWidget:
        """
        Return the ListModelWidget.
        """
        return ListModelWidget(queryset=Author.objects.all()[:10])


class AuthorListModelCardWidgetCard(CardWidget):
    """
    Wrapper around the :class:`~demo.core.wildewidgets.ListModelCardWidget` widget.
    """

    #: The title of the card.
    title: str = "List Model Card Widget"
    #: The icon of the card.
    icon = "person-square"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(AuthorListModelCardWidgetCard.get_author_list_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_author_list_widget())
        self.set_widget(tab, "mb-5")

    def get_author_list_widget(self) -> ListModelCardWidget:
        """
        Return the ListModelCardWidget.
        """
        return ListModelCardWidget(queryset=Author.objects.all()[:10])


class TabCard(CardWidget):
    """
    Wrapper around the :class:`~demo.core.wildewidgets.TabbedWidget` widget.
    """

    #: The title of the card.
    title: str = "Tab Widget"
    #: The icon of the card.
    icon: str = "tab"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(TabCard.get_tab_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_tab_widget())
        self.set_widget(tab, "mb-5")

    def get_tab_widget(self) -> TabbedWidget:
        """
        Return the TabbedWidget with two tabs.
        """
        tab = TabbedWidget()
        tab.add_tab("Tab 1", Block("This is tab 1"))
        tab.add_tab("Tab 2", Block("This is tab 2"))
        return tab


class CardCard(CardWidget):
    """
    Wrapper around the :class:`~demo.core.wildewidgets.CardWidget` widget.
    """

    #: The title of the card.
    title: str = "Card Widget"
    #: The icon of the card.
    icon: str = "card"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(CardCard.get_card_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_card_widget())
        self.set_widget(tab, "mb-5")

    def get_card_widget(self) -> CardWidget:
        """
        Return the CardWidget.
        """
        card = CardWidget(header_text="This is the card's header")
        card.set_widget(Block("This is a the card's content."))
        return card


class CrispyFormCard(CardWidget):
    """
    Wrapper around the :class:`~demo.core.wildewidgets.CrispyFormWidget` widget.
    """

    #: The title of the card.
    title: str = "Crispy Form Widget"
    #: The icon of the card.
    icon: str = "form"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(CrispyFormCard.get_crispy_form_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_crispy_form_widget())
        self.set_widget(tab, "mb-5")

    def get_crispy_form_widget(self) -> CrispyFormWidget:
        """
        Return the CrispyFormWidget.
        """
        form = MinimalBookForm()
        form.helper.form_method = "get"
        return CrispyFormWidget(form=form)


class CollapseCard(CardWidget):
    """
    Wrapper around the :class:`~demo.core.wildewidgets.CollapseWidget` widget.
    """

    #: The title of the card.
    title: str = "Collapse Widget"
    #: The icon of the card.
    icon: str = "collapse"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(CollapseCard.get_collapse_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_collapse_widget())
        self.set_widget(tab, "mb-5")

    def get_collapse_widget(self) -> Block:
        """
        Return the CollapseWidget.
        """
        header = CardHeader(header_text="Collapse Widget")
        header.add_collapse_button(
            text="Show Form",
            color="primary",
            target="#collapse1",
        )
        form = MinimalBookForm()
        form.helper.form_method = "get"
        form_widget = CollapseWidget(
            CrispyFormWidget(form=form),
            css_id="collapse1",
        )
        return Block(header, form_widget)


class HorizontalLayoutCard(CardWidget):
    """
    Wrapper around the :class:`~demo.core.wildewidgets.HorizontalLayoutBlock` widget.
    """

    #: The title of the card.
    title: str = "Horizontal Layout Widget"
    #: The icon of the card.
    icon: str = "layout"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(HorizontalLayoutCard.get_horizontal_layout_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_horizontal_layout_widget())
        self.set_widget(tab, "mb-5")

    def get_horizontal_layout_widget(self) -> HorizontalLayoutBlock:
        return HorizontalLayoutBlock(
            Block("This is a string block", css_class="border p-3 bg-azure"),
            Block("This is a string block", css_class="border p-3 bg-yellow"),
            Block("This is a string block", css_class="border p-3 bg-lime"),
            Block("This is a string block", css_class="border p-3 bg-cyan"),
        )


class ModalCard(CardWidget):
    """
    Wrapper around the :class:`~demo.core.wildewidgets.ModalWidget` widget.
    """

    #: The title of the card.
    title: str = "Modal Widget"
    #: The icon of the card.
    icon: str = "modal"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(ModalCard.get_modal_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_modal_widget())
        self.set_widget(tab, "mb-5")

    def get_modal_widget(self) -> Block:
        """
        Return the ModalWidget.
        """
        header = CardHeader(header_text="Modal Widget")
        header.add_modal_button(
            text="Show Modal",
            color="primary",
            target="#modal1",
        )
        modal = ModalWidget(
            modal_id="modal1",
            modal_title="Modal Title",
            modal_body="This is a modal widget",
        )
        return Block(header, modal)


class CrispyFormModalCard(CardWidget):
    """
    Wrapper around the :class:`~demo.core.wildewidgets.CrispyFormModalWidget` widget.
    """

    #: The title of the card.
    title: str = "Crispy Form Modal Widget"
    #: The icon of the card.
    icon: str = "form"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        code = get_code_block(CrispyFormModalCard.get_crispy_form_modal_widget)
        tab = WidgetCodeTab(code=code, widget=self.get_crispy_form_modal_widget())
        self.set_widget(tab, "mb-5")

    def get_crispy_form_modal_widget(self) -> Block:
        """
        Return the CrispyFormModalWidget.
        """
        header = CardHeader(header_text="Crispy Form Modal Widget")
        header.add_modal_button(
            text="Show Modal",
            color="primary",
            target="#modal2",
        )
        form = MinimalBookForm()
        form.helper.form_method = "get"
        modal = CrispyFormModalWidget(
            modal_id="modal2",
            modal_title="Modal Title",
            form=form,
        )
        return Block(header, modal)


class HomeTable(BasicModelTable):
    """
    Demonstration of the :class:`~demo.core.wildewidgets.BasicModelTable` widget.
    """

    #: The model of the table.
    model: type[Model] = Book
    #: The fields of the table.
    fields: ClassVar[list[str]] = ["title", "isbn", "binding"]  # type: ignore[misc]
    #: Whether to hide the controls.
    hide_controls: bool = True
    #: The page length of the table.
    page_length: int = 25
    #: Whether to stripe the table.
    striped: bool = True
    #: Whether to make the table small.
    small: bool = True
    #: Whether to make the table unsearchable.
    unsearchable: ClassVar[list[str]] = ["binding"]  # type: ignore[misc]


class AuthorListModelWidget(ListModelWidget):
    """
    Wrapper around the :class:`~demo.core.wildewidgets.ListModelWidget` widget.
    """

    def get_object_text(self, obj) -> str:
        """
        Return the object text.
        """
        return f"{FontIcon(icon='person-fill', css_class='pe-2')!s} {obj!s}"


class HomeBlock(Block):
    """
    Main block for the demo home page.
    """

    #: The description of the demo project
    description = """
django-wildewidgets is a Django design library providing several tools for
building full-featured, widget-based web applications with a standard,
consistent design, based on Bootstrap.
"""
    #: The features of wildewidgets.
    features: ClassVar[list[str]] = [
        "Large library of standard widgets",
        "Custom widgets",
        "Widgets can be composable",
        "Teplateless design",
        "AJAX data for tables, charts, and other data based widgets",
        "Several supporting views",
    ]
    #: The standard widgets of wildewidgets.
    standard_widgets: ClassVar[list[str]] = [
        "Basic blocks",
        "Template based widgets",
        "Basic Buttons",
        "Form, Modal, and Collapse Buttons",
        "Header widgets",
        "Chart widgets, including Altair, Apex, and ChartJS",
        "Layout and structural widgets, like Card and Tab widgets",
        "Modal widgets",
        "Form widgets",
        "Table widgets",
        "Text widgets, like HTML, Code, Markdown, and Label widgets",
        "Other miscillaneous widgets, like Breadcrumb, "
        "Gravatar, and KeyValueList widgets.",
    ]
    #: Footer notice for the demo project.
    notice: str = (
        "This entire site is built using django-wildewidgets, "
        "with only a single shared template."
    )

    def __init__(self, *args, **kwargs):  # noqa: ARG002
        header = PageHeader(
            header_text="django-wildewidgets Demo",
            css_class=f"{PageHeader.css_class} mx-1",
        )

        pie = PieChart(width=100, height=100)
        pie.set_categories(
            ["January", "February", "March", "April", "May", "June", "July"]
        )
        pie.add_dataset([75, 44, 92, 11, 44, 95, 35])

        modal = ModalWidget(
            modal_id="modal1",
            modal_title="Modal Title",
            modal_body=Block("This is a modal widget"),
        )

        super().__init__(
            header,
            CardWidget(
                widget=Block(
                    Block(self.description, css_class="w-75"),
                    Block(self.notice, css_class="w-75 my-3 fw-bold"),
                ),
                css_class="mb-2",
            ),
            HorizontalLayoutBlock(
                Block(
                    CardWidget(
                        header=BasicHeader(
                            header_text="Features", css_class="my-0", header_level=3
                        ),
                        widget=UnorderedList(*self.features),
                        css_class="mb-2",
                    ),
                    CardWidget(
                        header=BasicHeader(
                            header_text="Standard Widgets",
                            css_class="my-0",
                            header_level=3,
                        ),
                        widget=UnorderedList(*self.standard_widgets),
                        css_class="mb-2",
                    ),
                ),
                Block(
                    CardWidget(
                        widget=TestDoughnutChart(legend=False, width=240, height=300),
                        css_class="mb-2",
                    ),
                    CardWidget(
                        widget=HorizontalLayoutBlock(
                            ModalButton(
                                text=Block(
                                    FontIcon(icon="window", css_class="pe-1"), "Modal"
                                ),
                                color="primary",
                                target="#modal1",
                            ),
                            LinkButton(
                                url="https://github.com/caltechads/django-wildewidgets",
                                text=Block(
                                    TablerFontIcon(
                                        icon="brand-github", css_class="pe-1"
                                    ),
                                    "Github",
                                ),
                                color="secondary",
                            ),
                            justify="evenly",
                        ),
                        css_class="py-3 mb-2",
                    ),
                    CardWidget(
                        widget=AuthorListModelWidget(
                            queryset=Author.objects.all()[5:8]
                        ),
                        css_class="mb-2",
                        attributes={"style": "height: 223px;"},
                    ),
                    css_class="mx-xl-2",
                ),
                Block(
                    CardWidget(
                        widget=TestChart(width="300px", height="371px"),
                        css_class="mb-2",
                    ),
                    CardWidget(
                        widget=ApexLineChart(),
                        css_class="mb-2 pt-4",
                    ),
                ),
                align="start",
                flex_size="xl",
            ),
            CardWidget(
                widget=HomeTable(),
                css_class=" overflow-auto",
            ),
            modal,
        )
