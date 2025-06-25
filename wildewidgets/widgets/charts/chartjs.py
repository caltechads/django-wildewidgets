from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING, Final, Literal

from django import template
from django.conf import settings

from wildewidgets.views import JSONDataView, WidgetInitKwargsMixin

from ..base import Widget

if TYPE_CHECKING:
    from collections.abc import Generator, Iterator


def float_range(
    start: float, stop: float, step: float = 1.0
) -> Generator[float, None, None]:
    """
    A generator function that yields a range of floating point numbers.

    This function behaves like the built-in `range` function, but for floating point
    numbers. It yields numbers starting from `start`, up to but not including `stop`,
    incrementing by `step`.

    Example:
        >>> list(float_range(0.0, 5.0, 1.0))
        [0.0, 1.0, 2.0, 3.0, 4.0]

        >>> list(float_range(0.0, 5.0, 0.5))
        [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]

    Note:
        This function does not support negative steps or reverse ranges.

    Args:
        start: the starting value of the range.
        stop: the end value of the range (exclusive).
        step: the increment between each value in the range.

    Yields:
        float: the next value in the range.

    """
    current = start
    while current < stop:
        yield current
        current += step


class CategoryChart(Widget, WidgetInitKwargsMixin, JSONDataView):
    """
    Base class for Chart.js charts that display data in categories.

    This abstract class provides the foundation for creating various Chart.js
    visualizations that organize data into categories (like bar charts, pie
    charts, etc.).  It handles dataset management, color assignment, and
    rendering.

    Note:
        This is an abstract base class. Subclasses should implement the necessary
        methods to create specific chart types.

    Example:
        .. code-block:: python

            from wildewidgets import CategoryChart

            class MyBarChart(CategoryChart):
                def __init__(self, **kwargs):
                    super().__init__(chart_type="bar", **kwargs)
                    self.set_categories(['A', 'B', 'C'])
                    self.add_dataset([10, 20, 30], "Series 1")

    """

    #: Default colors for the chart, used if no custom colors are set
    COLORS: Final[list[tuple[int, int, int]]] = [
        (0, 59, 76),
        (0, 88, 80),
        (100, 75, 120),
        (123, 48, 62),
        (133, 152, 148),
        (157, 174, 136),
        (159, 146, 94),
        (242, 211, 131),
        (30, 152, 138),
        (115, 169, 80),
    ]

    #: Default grayscale colors for the chart, used if no custom colors are set
    GRAYS: Final[list[tuple[int, int, int]]] = [
        (200, 200, 200),
        (229, 229, 229),
        (170, 169, 159),
        (118, 119, 123),
        (97, 98, 101),
        (175, 175, 175),
        (105, 107, 115),
    ]
    #: The Django template file to render the chart
    template_file: str = "wildewidgets/categorychart.html"
    #: Display legend for the chart, can be set in options
    legend: bool = False
    #: Position of the legend, can be set in options
    legend_position: Literal["top", "bottom", "left", "right"] = "top"
    #: Whether to use the color palette (True) or grayscale (False)
    color: bool = True

    def __init__(self, *args, **kwargs):
        self.chart_options = {
            "width": kwargs.get("width", "400px"),
            "height": kwargs.get("height", "400px"),
            "title": kwargs.get("title"),
            "legend": kwargs.get("legend", self.legend),
            "legend_position": kwargs.get("legend_position", self.legend_position),
            "chart_type": kwargs.get("chart_type"),
            "histogram": kwargs.get("histogram", False),
            "max": kwargs.get("max"),
            "thousands": kwargs.get("thousands", False),
            "histogram_max": kwargs.get("histogram_max"),
            "url": kwargs.get("url"),
        }
        self.chart_id = kwargs.get("chart_id")
        self.categories = None
        self.datasets = []
        self.dataset_labels = []
        self.color = kwargs.get("color", self.color)
        self.colors = []
        if hasattr(settings, "CHARTJS_FONT_FAMILY"):
            self.chart_options["chartjs_font_family"] = settings.CHARTJS_FONT_FAMILY
        if hasattr(settings, "CHARTJS_TITLE_FONT_SIZE"):
            self.chart_options["chartjs_title_font_size"] = (
                settings.CHARTJS_TITLE_FONT_SIZE
            )
        if hasattr(settings, "CHARTJS_TITLE_FONT_STYLE"):
            self.chart_options["chartjs_title_font_style"] = (
                settings.CHARTJS_TITLE_FONT_STYLE
            )
        if hasattr(settings, "CHARTJS_TITLE_PADDING"):
            self.options["chartjs_title_padding"] = settings.CHARTJS_TITLE_PADDING
        super().__init__(*args, **kwargs)

    def set_categories(self, categories: list[str] | list[float]) -> None:
        """
        Set the categories for the chart's x-axis.

        Args:
            categories: List of category labels to display on the x-axis

        """
        self.categories = categories

    def add_dataset(
        self, dataset: list[float] | list[int], label: str | None = None
    ) -> None:
        """
        Add a dataset to the chart.

        Args:
            dataset: List of data values corresponding to each category
            label: Optional name for the dataset (shown in legend)

        """
        self.datasets.append(dataset)
        self.dataset_labels.append(label)

    def set_option(self, name: str, value: str | float | bool | None) -> None:
        """
        Set a chart configuration option.

        Args:
            name: The option name
            value: The option value

        """
        self.chart_options[name] = value

    def set_color(self, color: bool) -> None:
        """
        Enable or disable color mode.

        Args:
            color: If True, use the color palette; if False, use grayscale

        """
        self.color = color

    def set_colors(self, colors: list[tuple[int, int, int]]) -> None:
        """
        Set a custom color palette for the chart.

        Args:
            colors: List of RGB color tuples to use for chart elements

        """
        self.colors = colors

    def get_content(self, **kwargs):  # noqa: ARG002
        """
        Render the chart as HTML content.

        Returns:
            str: The rendered HTML for the chart

        """
        chart_id = self.chart_id if self.chart_id else str(random.randrange(0, 1000))  # noqa: S311
        template_file = self.template_file
        context = self.get_context_data() if self.datasets else {"async": True}
        html_template = template.loader.get_template(template_file)
        context["options"] = self.options
        context["name"] = f"chart_{chart_id}"
        context["wildewidgetclass"] = self.__class__.__name__
        context["extra_data"] = self.get_encoded_extra_data()
        return html_template.render(context)

    def __str__(self):
        """
        Return the string representation of the chart.

        Returns:
            str: The rendered HTML for the chart

        """
        return self.get_content()

    def get_context_data(self, **kwargs):
        """
        Get the context data for rendering the chart template.

        Returns:
            dict: The context data for the template

        """
        context = super().get_context_data(**kwargs)
        self.load()
        context.update(
            {"labels": self.get_categories(), "datasets": self.get_dataset_configs()}
        )
        return context

    def get_color_iterator(self) -> Iterator[tuple[int, int, int]]:
        """
        Get an iterator over the chart's color palette.

        Returns:
            iterator: Iterator over RGB color tuples

        """
        if self.colors:
            return iter(self.colors)
        if self.color:
            return iter(self.COLORS)
        return iter(self.GRAYS)

    def get_dataset_options(self, index, color: tuple[int, int, int]):  # noqa: ARG002
        """
        Get rendering options for a dataset.

        Args:
            index: The index of the dataset
            color: The RGB color tuple for the dataset

        Returns:
            dict: Dataset rendering options

        """
        return {
            "backgroundColor": f"rgba({color[0]}, {color[1]}, {color[2]}, 0.5)",
            "borderColor": f"rgba({color[0]}, {color[1]}, {color[2]}, 1)",
            "borderWidth": 0.2,
        }

    def get_dataset_configs(self) -> list[dict]:
        """
        Get the complete configuration for all datasets.

        Returns:
            list[dict]: List of dataset configuration dictionaries

        Note:
            This method should be implemented by subclasses.

        """
        return []

    def get_categories(self) -> list[str]:
        """
        Get the category labels for the chart.

        Returns:
            list[str]: List of category labels

        Raises:
            NotImplementedError: If not implemented by a subclass

        """
        if self.categories:
            return self.categories
        msg = 'You should return a labels list. (i.e: ["January", ...])'
        raise NotImplementedError(msg)

    def get_datasets(self) -> list[list[float]]:
        """
        Get all datasets for the chart.

        Returns:
            list[list[float]]: List of datasets, each containing values for each
                category

        Raises:
            NotImplementedError: If not implemented by a subclass

        """
        if self.datasets:
            return self.datasets
        msg = "You should return a data list list. (i.e: [[25, 34, 0, 1, 50], ...])."
        raise NotImplementedError(msg)

    def get_dataset_labels(self) -> list[str]:
        """
        Get labels for all datasets.

        Returns:
            list[str]: List of dataset labels

        """
        return self.dataset_labels

    def load(self) -> None:
        """
        Load data into the chart.

        This method should be implemented by subclasses to load data from
        external sources or perform calculations before rendering.
        """


class DoughnutChart(CategoryChart):
    """
    A doughnut chart implementation using Chart.js.

    This class creates a doughnut chart (a pie chart with a hole in the center)
    that displays data as segments of a circle. Each segment represents a
    proportion of the whole, making this chart ideal for showing composition.

    Example:
        .. code-block:: python

            chart = DoughnutChart(title="Browser Usage")
            chart.set_categories(['Chrome', 'Firefox', 'Safari', 'Edge', 'Other'])
            chart.add_dataset([65, 15, 10, 8, 2], "Usage Share")

    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize a doughnut chart.

        Args:
            *args: Positional arguments passed to the parent class
            **kwargs: Keyword arguments passed to the parent class
                chart_type: Set to "doughnut" by default if not specified

        """
        if "chart_type" not in kwargs:
            kwargs["chart_type"] = "doughnut"
        super().__init__(*args, **kwargs)

    def get_dataset_configs(self) -> list[dict]:
        """
        Configure datasets for the doughnut chart.

        For doughnut charts, each data point gets its own color in the
        backgroundColor array.

        Returns:
            list[dict]: List containing a single dataset configuration

        """
        datasets = []
        color_generator = self.get_color_iterator()
        data = self.get_dataset()
        dataset = {"data": data}
        dataset["backgroundColor"] = []
        for _ in range(len(data)):
            color = tuple(next(color_generator))
            dataset["backgroundColor"].append(
                f"rgba({color[0]}, {color[1]}, {color[2]}, 0.5)"
            )
        datasets.append(dataset)
        return datasets

    def get_dataset(self):
        """
        Get the primary dataset for the doughnut chart.

        Returns:
            list: The first dataset in the datasets list

        """
        return self.datasets[0]


class PieChart(DoughnutChart):
    """
    A pie chart implementation using Chart.js.

    This class creates a pie chart that displays data as segments of a circle.
    Each segment represents a proportion of the whole, making this chart ideal
    for showing composition.

    It extends DoughnutChart and has the same functionality, just with a different
    chart type.

    Example:
        .. code-block:: python

            from wildewidgets import PieChart

            chart = PieChart(title="Expenditure Breakdown")
            chart.set_categories(
                ['Housing', 'Food', 'Transport', 'Entertainment', 'Other']
            )
            chart.add_dataset([35, 25, 15, 15, 10], "Percentage")

    """

    def __init__(self, *args, **kwargs):
        """
        Initialize a pie chart.

        Args:
            *args: Positional arguments passed to the parent class
            **kwargs: Keyword arguments passed to the parent class

        Note:
            Automatically sets chart_type to "pie"

        """
        kwargs["chart_type"] = "pie"
        super().__init__(*args, **kwargs)


class BarChart(CategoryChart):
    """
    A bar chart implementation using Chart.js.

    This class creates a vertical bar chart where data is displayed as rectangular
    bars with heights proportional to their values. Bar charts are excellent for
    comparing quantities across different categories.

    Features:

    - Support for multiple datasets (grouped bars)
    - Optional stacking of bars
    - Horizontal orientation option
    - Money formatting option

    Example:
        .. code-block:: python

            from wildewidgets import BarChart

            chart = BarChart(title="Monthly Sales")
            chart.set_categories(['Jan', 'Feb', 'Mar', 'Apr', 'May'])
            chart.add_dataset([10000, 15000, 12000, 18000, 20000], "2022")
            chart.add_dataset([12000, 18000, 15000, 21000, 25000], "2023")

    """

    def __init__(self, *args, **kwargs):
        """
        Initialize a bar chart.

        Args:
            *args: Positional arguments passed to the parent class

        Keyword Args:
            **kwargs: Keyword arguments passed to the parent class
                chart_type: Set to "bar" by default if not specified
                money: Whether to format values as currency (default: False)
                stacked: Whether to stack multiple datasets (default: False)
                xAxes_name: Name for x-axis configuration (default: "xAxes")
                yAxes_name: Name for y-axis configuration (default: "yAxes")

        """
        if "chart_type" not in kwargs:
            kwargs["chart_type"] = "bar"
        super().__init__(*args, **kwargs)
        self.set_option("money", kwargs.get("money", False))
        self.set_option("stacked", kwargs.get("stacked", False))
        self.set_option("xAxes_name", kwargs.get("xAxes_name", "xAxes"))
        self.set_option("yAxes_name", kwargs.get("yAxes_name", "yAxes"))

    def set_stacked(self, stacked: bool) -> None:
        """
        Enable or disable stacked mode for the bar chart.

        In stacked mode, bars from different datasets are stacked on top of
        each other instead of being displayed side by side.

        Args:
            stacked: If True, enable stacked mode; if False, disable it

        """
        self.set_option("stacked", "true" if stacked else "false")

    def set_horizontal(self, horizontal: bool) -> None:
        """
        Set the orientation of the bar chart.

        Args:
            horizontal: If True, display bars horizontally; if False, display vertically

        """
        if horizontal:
            self.chart_options["xAxes_name"] = "yAxes"
            self.chart_options["yAxes_name"] = "xAxes"
            self.chart_options["chart_type"] = "horizontalBar"
        else:
            self.chart_options["xAxes_name"] = "xAxes"
            self.chart_options["yAxes_name"] = "yAxes"
            self.chart_options["chart_type"] = "bar"

    def get_dataset_options(self, index, color: tuple[int, int, int]):  # noqa: ARG002
        """
        Get rendering options for a dataset in the bar chart.

        Args:
            index: The index of the dataset
            color: The RGB color tuple for the dataset

        Returns:
            dict: Dataset rendering options with appropriate styling

        """
        default_opt: dict[str, str | float] = {
            "backgroundColor": f"rgba({color[0]}, {color[1]}, {color[2]}, 0.65)",
        }
        if not self.chart_options["histogram"]:
            default_opt["borderColor"] = f"rgba({color[0]}, {color[1]}, {color[2]}, 1)"
            default_opt["borderWidth"] = 0.2
        return default_opt

    def get_dataset_configs(self) -> list[dict]:
        """
        Get the complete configuration for all datasets in the bar chart.

        This method prepares all datasets with appropriate colors and options.

        Returns:
            list[dict]: List of dataset configuration dictionaries

        """
        datasets = []
        color_generator = self.get_color_iterator()
        data = self.get_datasets()
        dataset_labels = self.get_dataset_labels()
        num = len(dataset_labels)
        for i, entry in enumerate(data):
            color = next(color_generator)
            dataset: dict[str, str | float | list[float]] = {"data": entry}
            dataset.update(self.get_dataset_options(i, color))
            if i < num:
                dataset["label"] = dataset_labels[i]  # series labels for Chart.js
                dataset["name"] = dataset_labels[i]  # HighCharts may need this
            datasets.append(dataset)
        return datasets


class StackedBarChart(BarChart):
    """
    A stacked bar chart implementation using Chart.js.

    This class creates a vertical bar chart where multiple datasets are stacked
    on top of each other for each category. This is useful for comparing total
    values across categories while also showing the composition of each total.

    Example:
        .. code-block:: python

            from wildewidgets import StackedBarChart

            chart = StackedBarChart(title="Revenue Breakdown")
            chart.set_categories(['Q1', 'Q2', 'Q3', 'Q4'])
            chart.add_dataset([50000, 60000, 55000, 75000], "Product A")
            chart.add_dataset([35000, 40000, 45000, 55000], "Product B")
            chart.add_dataset([15000, 20000, 25000, 30000], "Product C")

    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize a stacked bar chart.

        Args:
            *args: Positional arguments passed to the parent class
            **kwargs: Keyword arguments passed to the parent class

        Note:
            Automatically enables stacked mode during initialization.

        """
        super().__init__(*args, **kwargs)
        self.set_stacked(True)


class HorizontalBarChart(BarChart):
    """
    A horizontal bar chart implementation using Chart.js.

    This class creates a horizontal bar chart where data is displayed as
    rectangular bars with lengths proportional to their values. Horizontal
    bar charts are excellent for comparing quantities across different
    categories, especially when category labels are long.

    Example:
        .. code-block:: python

            from wildewidgets import HorizontalBarChart

            chart = HorizontalBarChart(title="Population by Country")
            chart.set_categories(
               ['United States', 'Indonesia', 'Brazil', 'Russia', 'Mexico']
            )
            chart.add_dataset(
                [331000000, 273500000, 211800000, 145500000, 130000000], "Population"
            )

    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize a horizontal bar chart.

        Args:
            *args: Positional arguments passed to the parent class
            **kwargs: Keyword arguments passed to the parent class

        Note:
            Automatically sets horizontal orientation during initialization.

        """
        super().__init__(*args, **kwargs)
        self.set_horizontal(True)


class HorizontalStackedBarChart(BarChart):
    """
    A horizontal stacked bar chart implementation using Chart.js.

    This class creates a horizontal bar chart where multiple datasets are stacked
    on top of each other for each category. Useful for comparing parts of a whole
    across different categories.

    The chart is configured with both horizontal orientation and stacked mode
    automatically during initialization.

    Examples:
        .. code-block:: python

            from wildewidgets import HorizontalStackedBarChart

            chart = HorizontalStackedBarChart()
            chart.set_categories(['A', 'B', 'C'])
            chart.add_dataset([10, 20, 30], "Dataset 1")
            chart.add_dataset([5, 15, 25], "Dataset 2")

    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize a horizontal stacked bar chart.

        Args:
            *args: Positional arguments passed to the parent class
            **kwargs: Keyword arguments passed to the parent class

        Note:
            Automatically configures the chart as both horizontal and stacked.

        """
        super().__init__(*args, **kwargs)
        self.set_horizontal(True)
        self.set_stacked(True)


class Histogram(BarChart):
    """
    A vertical histogram chart for visualizing data distribution.

    This class creates a histogram that displays the distribution of numerical data
    by grouping values into bins. The height of each bar represents the frequency
    of values within that bin.

    To use this chart, call the `build` method with your raw data and the desired
    number of bins. The class will automatically:
    1. Calculate appropriate bin ranges
    2. Count values in each bin
    3. Configure the chart with proper categories and dataset

    Examples:
        .. code-block:: python

            # Create a histogram with 10 bins for a list of data points
            chart = Histogram(title="Distribution of Values")
            chart.build([23.5, 24.1, 25.3, 26.2, 27.5, 28.1, 29.3, 30.2, 31.5], 10)

    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize a histogram chart.

        Args:
            *args: Positional arguments passed to the parent class
            **kwargs: Keyword arguments passed to the parent class
                histogram: Flag to enable histogram mode (set to True by default)

        """
        if "histogram" not in kwargs:
            kwargs["histogram"] = True
        super().__init__(*args, **kwargs)

    def build(self, data: list[float], bin_count: int) -> None:
        """
        Process raw data and configure the histogram.

        This method handles all the calculations needed to convert raw data into
        a histogram representation:
        - Determines the range of the data
        - Calculates appropriate bin sizes and boundaries
        - Counts the frequency of values in each bin
        - Sets up the chart categories and dataset

        The method uses a robust algorithm that handles both positive and negative
        values, and attempts to create visually appealing bin boundaries.

        Args:
            data: List of numerical values to be plotted in the histogram
            bin_count: Number of bins to divide the data into

        Note:
            The method will set two special options on the chart:
            - "max": The upper bound of the last visible bin
            - "histogram_max": The absolute upper boundary of the data range

        """
        num_min = min(data)
        num_max = max(data)

        num_range = num_max - num_min
        bin_chunk = num_range / bin_count
        bin_power = math.floor(math.log10(bin_chunk))
        bin_chunk = math.ceil(bin_chunk / 10**bin_power) * 10**bin_power
        if num_min < 0:
            bin_min = math.ceil(math.fabs(num_min / bin_chunk)) * bin_chunk * -1
        else:
            bin_min = math.floor(num_min / bin_chunk) * bin_chunk
        if num_max < 0:
            bin_max = math.floor(math.fabs(num_max / bin_chunk)) * bin_chunk * -1
        else:
            bin_max = math.ceil(num_max / bin_chunk) * bin_chunk
        categories = list(float_range(bin_min, bin_max + bin_chunk, bin_chunk))
        self.set_option("max", categories[-2])
        self.set_option("histogram_max", categories[-1])
        bins = [0] * bin_count
        for num in data:
            for i in range(len(categories) - 1):
                if num >= categories[i] and num < categories[i + 1]:
                    if i < len(bins):
                        bins[i] += 1
        self.set_categories(categories)
        self.add_dataset(bins, "data")


class HorizontalHistogram(Histogram):
    """
    A horizontal histogram chart for visualizing data distribution.

    This class extends the regular Histogram to display bars horizontally instead
    of vertically. This can be particularly useful when:
    - You have many bins that would appear too narrow in a vertical histogram
    - You want to display long category labels that are easier to read horizontally
    - You want to emphasize the comparison of frequencies across bins

    All the functionality of the regular Histogram is preserved, including the
    automatic calculation of bin ranges and frequencies.

    Examples:
        .. code-block:: python

            # Create a horizontal histogram with 8 bins
            chart = HorizontalHistogram(title="Age Distribution")
            chart.build([21, 22, 24, 25, 26, 28, 29, 31, 32, 33, 35, 37, 39, 45], 8)

    """

    def __init__(self, *args, **kwargs):
        """
        Initialize a horizontal histogram chart.

        Args:
            *args: Positional arguments passed to the parent class
            **kwargs: Keyword arguments passed to the parent class

        Note:
            Automatically configures the chart with horizontal orientation while
            preserving all histogram functionality.

        """
        super().__init__(*args, **kwargs)
        self.set_horizontal(True)
