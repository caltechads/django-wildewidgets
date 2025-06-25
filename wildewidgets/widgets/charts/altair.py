from __future__ import annotations

import random
from typing import Any

from django import template

from wildewidgets.views import JSONDataView

from ..base import Widget


class AltairChart(Widget, JSONDataView):
    """
    A widget for rendering Altair charts in Django applications.

    This class provides a wrapper around Altair charts, making them easy to integrate
    into Django templates. It supports both synchronous and asynchronous loading of
    chart data, and allows for customization of the chart's appearance.

    The chart content is rendered using a Django template, and the chart data is
    loaded via a JSON endpoint when in asynchronous mode.

    Example:
        .. code-block:: python

            import altair as alt
            from wildewidgets.widgets.charts.altair import AltairChart

            class MyBarChart(AltairChart):
                def load(self):
                    # Create an Altair chart
                    data = pd.DataFrame({
                        'category': ['A', 'B', 'C'],
                        'value': [10, 20, 30]
                    })
                    chart = alt.Chart(data).mark_bar().encode(
                        x='category',
                        y='value'
                    )
                    self.set_data(chart)

    """

    #: The Django template file to render the chart
    template_file: str = "wildewidgets/altairchart.html"
    #: The title of the chart, can be set in the options
    title: str | None = None
    #: Default width for the chart, can be overridden in options
    width: str = "100%"
    #: Default height for the chart, can be overridden in options
    height: str = "300px"

    def __init__(self, *args, **kwargs) -> None:  # noqa: ARG002
        """
        Initialize the Altair chart widget.

        Args:
            *args: Variable length argument list (not used)
            **kwargs: Arbitrary keyword arguments
                width: Override the default chart width
                height: Override the default chart height
                title: Set the chart title

        Note:
            The chart data is not loaded during initialization. It will be
            loaded when get_context_data is called.

        """
        self.data = None
        self.chart_options = {
            "width": kwargs.get("width", self.width),
            "height": kwargs.get("height", self.height),
            "title": kwargs.get("title", self.title),
        }

    def get_content(self, **kwargs) -> str:  # noqa: ARG002
        """
        Render the chart as HTML content.

        This method renders the chart using the specified template file. If the chart
        data has not been loaded yet, it will set the ``async`` flag to
        ``True``, which tells the template to load the data asynchronously via a
        JSON endpoint.

        Args:
            **kwargs: Arbitrary keyword arguments (not used)

        Returns:
            str: The rendered HTML content for the chart

        """
        chart_id = random.randrange(0, 1000)  # noqa: S311
        template_file = self.template_file
        context: dict[str, Any] = (
            self.get_context_data() if self.data else {"async": True}
        )
        html_template = template.loader.get_template(template_file)
        context["options"] = self.chart_options
        context["name"] = f"altair_chart_{chart_id}"
        context["wildewidgetclass"] = self.__class__.__name__
        return html_template.render(context)

    def __str__(self) -> str:
        """
        Return the string representation of the chart.

        This method allows the chart to be used directly in Django templates.

        Returns:
            str: The rendered HTML content for the chart

        """
        return self.get_content()

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """
        Get the context data for rendering the chart.

        This method loads the chart data if it hasn't been loaded yet and
        adds it to the context data.

        Args:
            **kwargs: Arbitrary keyword arguments passed to the parent method

        Returns:
            dict: The context data for rendering the chart

        """
        context = super().get_context_data(**kwargs)
        self.load()
        context.update({"data": self.data})
        return context

    def set_data(self, spec, set_size: bool = True):
        """
        Set the chart data from an Altair chart specification.

        This method converts an Altair chart specification into a dictionary
        representation that can be serialized to JSON. It also optionally sets
        the chart to use container-based sizing.

        Args:
            spec: The Altair chart specification
            set_size: Whether to set the chart to use container-based sizing
                When True, the chart will fill its container element.
                When False, the chart will use its own width and height settings.

        """
        if set_size:
            self.data = spec.properties(width="container", height="container").to_dict()
        else:
            self.data = spec.to_dict()

    def load(self) -> None:
        """
        Load the chart data.

        This method should be overridden by subclasses to load the chart data.
        The implementation should create an Altair chart and call set_data() with it.

        The default implementation does nothing.

        Example:
            .. code-block:: python

                def load(self):
                    # Load data from a source
                    data = pd.DataFrame(...)

                    # Create an Altair chart
                    chart = alt.Chart(data).mark_bar().encode(...)

                    # Set the chart data
                    self.set_data(chart)

        """
