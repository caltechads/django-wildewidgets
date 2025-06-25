from __future__ import annotations

import json
import random
from typing import TYPE_CHECKING, Any, cast

from django import template
from django.http import JsonResponse

from wildewidgets.views import WidgetInitKwargsMixin

from ..base import Widget

if TYPE_CHECKING:
    from django.http.request import HttpRequest


class ApexDatasetBase(Widget):
    """
    Base class for Apex chart datasets.

    This class provides the foundation for defining datasets that can be added to
    ApexCharts. It handles the transformation of Python data into the format
    expected by the ApexCharts JavaScript library.

    Attributes:
        name: The name of the dataset, displayed in legends and tooltips
        chart_type: The specific chart type for this dataset (e.g., 'line', 'bar')
        data: The list of data points for this dataset

    Example:
        .. code-block:: python

            class MyDataset(ApexDatasetBase):
                name = "Monthly Sales"
                chart_type = "line"

                def __init__(self, **kwargs):
                    super().__init__(**kwargs)
                    self.data = [10, 41, 35, 51, 49, 62, 69, 91, 148]


        Or use subclassing to customize the dataset further:

        .. code-block:: python

            class CustomDataset(ApexDatasetBase):
                name = "Custom Data"
                chart_type = "bar"

                def __init__(self, **kwargs):
                    super().__init__(**kwargs)
                    self.data = self.load_custom_data()

                def load_custom_data(self) -> list[int]:
                    # Load or generate custom data here
                    return [5, 15, 25, 35, 45]

    """

    name: str | None = None
    chart_type: str | None = None

    def __init__(self, **kwargs: Any) -> None:  # noqa: ARG002
        """
        Initialize the dataset with empty data.

        Args:
            **kwargs: Additional keyword arguments (not used in base class)

        """
        self.data: list[Any] = []

    def get_options(self) -> dict[str, Any]:
        """
        Get the dataset options in the format expected by ApexCharts.

        This method transforms the dataset's properties into a dictionary format
        that can be serialized to JSON and used by the ApexCharts JavaScript library.

        Returns:
            dict: The dataset configuration options

        """
        options: dict[str, Any] = {"data": self.data}
        if self.name:
            options["name"] = self.name if self.name is not None else ""
        if self.chart_type:
            options["type"] = self.chart_type
        return options


class ApexJSONMixin:
    """
    A mixin class adding AJAX support to Apex Charts.

    This mixin enables Apex charts to load their data asynchronously via AJAX.
    It handles the HTTP request/response cycle and provides methods for
    preparing the chart data as JSON.

    Attributes:
        template_name: The Django template file for rendering the AJAX-enabled chart
        chart_options: Dictionary containing the chart configuration

    Note:
        Classes using this mixin should implement the `load` method to populate
        the chart's datasets.

    """

    template_name: str = "wildewidgets/apex_json.html"
    chart_options: dict[str, Any]

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        """
        Dispatch the request to the appropriate handler method.

        This method delegates to the appropriate HTTP method handler (e.g., get, post)
        based on the request method.

        Args:
            request: The HTTP request object
            *args: Additional positional arguments

        Keyword Arguments:
            **kwargs: Additional keyword arguments

        Returns:
            JsonResponse: The JSON response containing chart data

        """
        handler = getattr(self, cast("str", request.method).lower())
        return handler(request, *args, **kwargs)

    def get(self, _: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:  # noqa: ARG002
        """
        Handle GET requests for chart data.

        This method is called when the client makes an AJAX GET request for
        chart data. It returns the chart's series data as JSON.

        Args:
            _: The HTTP request object (unused)
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            JsonResponse: The JSON response containing chart data

        """
        data = self.get_series_data()
        return self.render_to_response(data)

    def render_to_response(
        self,
        context: dict[str, Any],
        **response_kwargs: Any,  # noqa: ARG002
    ) -> JsonResponse:
        """
        Render the chart data as a JSON response.

        Args:
            context: The chart data to be serialized as JSON

        Keyword Arguments:
            **response_kwargs: Additional keyword arguments (unused)

        Returns:
            JsonResponse: The JSON response containing chart data

        """
        return JsonResponse(context)

    def get_series_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Get the chart series data.

        This method loads the chart data and adds the series to the provided
        keyword arguments.

        Keyword Args:
            **kwargs: Keyword arguments to update with series data

        Returns:
            dict: The updated keyword arguments containing series data

        """
        self.load()
        kwargs["series"] = self.chart_options["series"]
        return kwargs

    def load(self) -> None:
        """
        Load datasets into the chart via AJAX.

        This method should be overridden by subclasses to populate the chart's
        datasets. It will be called when an AJAX request is made for chart data.

        Example:
            .. code-block:: python

                def load(self) -> None:
                    dataset = MyDataset()
                    dataset.data = [10, 41, 35, 51, 49, 62, 69, 91, 148]
                    self.add_dataset(dataset)

        """


class ApexChartBase(WidgetInitKwargsMixin):
    """
    Base class for Apex Charts in Django applications.

    This class provides the foundation for creating interactive Apex charts
    in Django applications. It handles chart configuration, dataset management,
    and rendering.

    Attributes:
        template_name: The Django template file for rendering the chart
        css_id: The HTML ID attribute for the chart container
        chart_type: The type of chart (e.g., 'line', 'bar', 'pie')
        chart_options: Dictionary containing all chart configuration options

    Example:
        .. code-block:: python

            class MyLineChart(ApexChartBase):
                chart_type = 'line'

                def __init__(self, **kwargs):
                    super().__init__(**kwargs)
                    dataset = MyDataset()
                    dataset.data = [10, 41, 35, 51, 49, 62, 69, 91, 148]
                    self.add_dataset(dataset)
                    self.add_categories(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                        'Jul', 'Aug', 'Sep'])

    """

    template_name: str = "wildewidgets/apex_chart.html"
    css_id: str | int | None = None
    chart_type: str | None = None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the Apex chart.

        Args:
            *args: Positional arguments passed to parent class

        Keyword Args:
            **kwargs: Keyword arguments
                css_id: Optional HTML ID for the chart container

        """
        super().__init__(*args, **kwargs)
        self.chart_options: dict[str, Any] = {}
        self.chart_options["series"] = []
        self.css_id = kwargs.get("css_id", self.css_id)
        self.chart_options["chart"] = {}
        if self.chart_type:
            self.chart_options["chart"]["type"] = self.chart_type

    def add_dataset(self, dataset: ApexDatasetBase) -> None:
        """
        Add a dataset to the chart.

        This method adds a dataset to the chart's series. Each dataset represents
        a data series in the chart (e.g., a line in a line chart or a set of bars
        in a bar chart).

        Args:
            dataset: The dataset to add to the chart

        """
        self.chart_options["series"].append(dataset.get_options())

    def add_categories(self, categories: list[Any]) -> None:
        """
        Set the categories for the chart's x-axis.

        This method sets the labels for the x-axis categories. These are typically
        used for categorical data like months, product names, etc.

        Args:
            categories: List of category labels

        """
        if "xaxis" not in self.chart_options:
            self.chart_options["xaxis"] = {}
        self.chart_options["xaxis"]["categories"] = categories

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Get the context data for rendering the chart template.

        This method prepares the data needed by the Django template to render
        the chart, including chart options, CSS ID, and extra data.

        Keyword Args:
            **kwargs: Additional context data

        Returns:
            dict: The context data for the template

        """
        kwargs["options"] = json.dumps(self.chart_options)
        if not self.css_id:
            self.css_id = str(random.randint(1, 100000))  # noqa: S311
        kwargs["css_id"] = self.css_id
        kwargs["wildewidgetclass"] = self.__class__.__name__
        kwargs["extra_data"] = self.get_encoded_extra_data()
        return kwargs

    def add_suboption(self, option: str, name: str, value: Any) -> None:
        """
        Add a nested configuration option to the chart.

        This method adds a configuration option to a nested section of the chart
        options. It's useful for setting options in sections like 'chart', 'xaxis',
        'yaxis', etc.

        Args:
            option: The parent option section (e.g., 'chart', 'xaxis')
            name: The name of the specific option
            value: The value to set for the option

        Example:
            .. code-block:: python

                # Set chart.height = 350
                chart.add_suboption('chart', 'height', 350)

                # Set tooltip.enabled = False
                chart.add_suboption('tooltip', 'enabled', False)

        """
        if option not in self.chart_options:
            self.chart_options[option] = {}
        self.chart_options[option][name] = value

    def __str__(self) -> str:
        """
        Return the HTML representation of the chart.

        This method allows the chart to be used directly in Django templates.

        Returns:
            str: The rendered HTML for the chart

        """
        return self.get_content()

    def get_content(self, **kwargs: Any) -> str:  # noqa: ARG002
        """
        Render the chart as HTML content.

        This method renders the chart using the specified template and context data.

        Args:
            **kwargs: Additional context data (unused)

        Returns:
            str: The rendered HTML content for the chart

        """
        context = self.get_context_data()
        html_template = template.loader.get_template(self.template_name)
        return html_template.render(context)


class ApexSparkline(ApexChartBase):
    """
    A specialized Apex chart for creating sparklines.

    Sparklines are small, simple, condensed charts typically shown inline with
    text or in a dashboard. This class configures an Apex chart with the
    appropriate settings for a sparkline visualization.

    Attributes:
        width: The width of the sparkline chart in pixels
        stroke_width: The width of the line/stroke in pixels

    Example:
        .. code-block:: python

            sparkline = ApexSparkline()
            dataset = MyDataset()
            dataset.data = [10, 41, 35, 51, 49, 62, 69, 91, 148]
            sparkline.add_dataset(dataset)

        Or use subclassing to customize the sparkline further:

        ... code-block:: python

            class CustomSparkline(ApexSparkline):
                width = 100
                stroke_width = 3

                def __init__(self, **kwargs):
                    super().__init__(**kwargs)
                    self.add_suboption("chart", "sparkline", {"enabled": True})
                    self.add_suboption("chart", "width", self.width)
                    self.add_suboption("stroke", "width", self.stroke_width)
                    self.add_dataset(self.get_dataset())

                def get_dataset(self) -> list[Any]:
                    # do your custom data loading here
                    return (
                        Model.objects
                        .order_by('datestamp')
                        .values_list('field_name', flat=True)
                    )

    """

    width: int = 65
    stroke_width: int = 2

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the sparkline chart with appropriate options.

        Args:
            **kwargs: Keyword arguments passed to the parent class

        """
        super().__init__(**kwargs)
        self.add_suboption("chart", "sparkline", {"enabled": True})
        self.add_suboption("chart", "width", self.width)
        self.add_suboption("stroke", "width", self.stroke_width)
