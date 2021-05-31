***************
Business Charts
***************

Business charts use a subset of ChartJS to build basic charts. Types include Bar, Horizontal Bar, Stacked Bar, Pie, Doughnut, and Histogram.

Usage
=====

Without AJAX
------------

With a chart that doesn't use ajax, the data will load before the page has been loaded. Large datasets may cause the page to load too slowly, so this is best for smaller datasets.

In your view code, import the appropriate chart::

    from wildewidgets import (
        BarChart, 
        DoughnutChart,
        HorizontalStackedBarChart, 
        HorizontalBarChart, 
        PieChart, 
        StackedBarChart, 
    )

and define the chart in your view::

    class HomeView(TemplateView):
        template_name = "core/home.html"

        def get_context_data(self, **kwargs):
            barchart = HorizontalStackedBarChart(title="New Customers Through July", money=True, legend=True, width='500', color=False)
            barchart.set_categories(["January", "February", "March", "April", "May", "June", "July"])
            barchart.add_dataset([75, 44, 92, 11, 44, 95, 35], "Central")
            barchart.add_dataset([41, 92, 18, 35, 73, 87, 92], "Eastside")
            barchart.add_dataset([87, 21, 94, 13, 90, 13, 65], "Westside")
            kwargs['barchart'] = barchart
            return super().get_context_data(**kwargs)    

In your template, simply display the chart::

    {{barchart}}

With Ajax
---------

With a chart that does use ajax, the data will load after the page has been loaded. This is the best choice for performance with large datasets, especially if you have multiple charts loading on a page. With ajax, the charts load in the background.

Create a file called ``wildewidgets.py`` in your app directory and create a new class derived from the chart class that you want. You'll need to either override ``get_categories``, ``get_dataset_labels`` and ``get_datasets``, or override ``load``, where you can just call the functions you need to call to set up your chart::

    from wildewidgets import StackedBarChart

    class TestChart(StackedBarChart):

        def get_categories(self):
            """Return 7 labels for the x-axis."""
            return ["January", "February", "March", "April", "May", "June", "July"]

        def get_dataset_labels(self):
            """Return names of datasets."""
            return ["Central", "Eastside", "Westside", "Central2", "Eastside2", "Westside2", "Central3", "Eastside3", "Westside3"]

        def get_datasets(self):
            """Return 3 datasets to plot."""

            return [[750, 440, 920, 1100, 440, 950, 350],
                    [410, 1920, 180, 300, 730, 870, 920],
                    [870, 210, 940, 3000, 900, 130, 650],
                    [750, 440, 920, 1100, 440, 950, 350],
                    [410, 920, 180, 2000, 730, 870, 920],
                    [870, 210, 940, 300, 900, 130, 650],
                    [750, 440, 920, 1100, 440, 950, 3500],
                    [410, 920, 180, 3000, 730, 870, 920],
                    [870, 210, 940, 300, 900, 130, 650]]

Then in your view code, use this class instead::

    from .wildewidgets import TestChart

    class HomeView(TemplateView):
        template_name = "core/home.html"

        def get_context_data(self, **kwargs):
            kwargs['barchart'] = TestChart(width='500', height='400', thousands=True)
            return super().get_context_data(**kwargs)    

In your template, display the chart as before::

    {{barchart}}

Histograms
----------

Histograms are built slightly differently. You'll need to call the object's ``build`` function, with arguments for a list of values, and the number of bins you want. The histogram will utilize ajax if the build function is called in the ``load`` function.

Without AJAX
^^^^^^^^^^^^

::

    class TestHistogram(Histogram): # without ajax

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            mu = 0
            sigma = 50
            nums = []
            bin_count = 40
            for i in range(10000):
                temp = random.gauss(mu,sigma)
                nums.append(temp)

            self.build(nums, bin_count)

With AJAX
^^^^^^^^^

::

    class TestHorizontalHistogram(HorizontalHistogram): # with ajax

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.set_color(False)

        def load(self):
            mu = 100
            sigma = 30
            nums = []
            bin_count = 50
            for i in range(10000):
                temp = random.gauss(mu,sigma)
                nums.append(temp)

            self.build(nums, bin_count)

Options
=======

There are a number of available Charts:

* BarChart
* HorizontalBarChart
* StackedBarChart
* HorizontalStackedBarChart
* PieChart
* DoughnutChart
* Histogram
* HorizontalHistogram

There are a number of options you can set for a specific chart::

    width: chart width in pixels (default: 400)
    height: chart height in pixels (default: 400)
    title: title text (default: None)
    color: use color as opposed to grayscale (default: True)
    legend: whether or not to show the legend - True/False (default: False)
    legend-position: top, right, bottom, left (default: left)
    thousands: if set to true, numbers are abbreviated as in 1K 5M, ... (default: False)
    money: whether or not the value is money (default: False)
    url: a click on a segment of a chart will redirect to this URL, with parameters label and value

Colors
------

You can also customize the colors by either overriding the class variable ``COLORS`` or calling the member function ``set_colors``. The format is a list of RGB tuples.

Fonts
-----

To customize the fonts globally, the available Django settings are::

    CHARTJS_FONT_FAMILY = "'Vaud', sans-serif"
    CHARTJS_TITLE_FONT_SIZE = '18'
    CHARTJS_TITLE_FONT_STYLE = 'normal'
    CHARTJS_TITLE_PADDING = '0'
