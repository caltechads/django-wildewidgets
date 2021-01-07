# Django Wildewidgets

django-wildewidgets is a Django library designed to help you make charts, graphs, tables, and UI widgets 
quickly and easily with libraries like Chartjs, Altair, and Datatables.

## Table of Contents

 * [Quick Start](#quick-start)
 * [Business Charts Usage](#business-charts-usage)
 * [Scientific Charts Usage](#scientific-charts-and-graphs-usage)
 * [Tables Usage](#tables-usage)
 * [Business Charts Options](#business-charts-options)
 * [Scientific Charts Options](#scientific-charts-and-options)
 * [Table Options](#table-options)

## Quick start

Install:

    pip install django-wildewidgets

If you plan on using [Altair charts](https://github.com/altair-viz/altair), run:

    pip install altair

If you plan on using [Datatables](https://https://datatables.net/), which use [django-datatables-view](https://bitbucket.org/pigletto/django-datatables-view/), run:

    pip install django-datatables-view

Add "wildewidgets" to your INSTALLED_APPS setting like this:

    INSTALLED_APPS = [
        ...
        'wildewidgets',
    ]


Include the wildewidgets URLconf in your project urls.py like this:

    from wildewidgets import WildewidgetDispatch

    urlpatterns = [
        ...
        path('<urlbasepath>/wildewidgets_json', WildewidgetDispatch.as_view(), name='wildewidgets_json'),
    ]


Add the appropriate resources to your template files.

For [ChartJS](https://www.chartjs.org/) (regular business type charts), add the corresponding javascript file:

    <script src="https://cdn.jsdelivr.net/npm/chart.js@2.9.4/dist/Chart.min.js"></script> 

For [Altair](https://github.com/altair-viz/altair) (scientific charts), use:

    <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
    <script src="https://cdn.jsdelivr.net/npm/vega-lite@4"></script>
    <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>  

And for [DataTables](https://github.com/DataTables/DataTables), use:

    <script src="https://cdn.datatables.net/1.10.21/js/jquery.dataTables.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.8.4/moment.min.js"></script>
    <script src="https://cdn.datatables.net/plug-ins/1.10.21/sorting/datetime-moment.js"></script>

and:

    <link href="https://cdn.datatables.net/1.10.21/css/jquery.dataTables.min.css" rel="stylesheet" />

## Business Charts Usage

### Without Ajax

With a chart that doesn't use ajax, the data will load before the page has been loaded. Large datasets may cause the page to load too slowly, so this is best for smaller datasets.

In your view code, import the appropriate chart:

    from wildewidgets import (
        BarChart, 
        DoughnutChart,
        HorizontalStackedBarChart, 
        HorizontalBarChart, 
        PieChart, 
        StackedBarChart, 
    )

and define the chart in your view:

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

In your template, simply display the chart:

    {{barchart}}

### With Ajax

With a chart that does use ajax, the data will load after the page has been loaded. This is the best choice for performance with large datasets, especially if you have multiple charts loading on a page. With ajax, the charts load in the background.

Create a file called `wildewidgets.py` in your app directory and create a new class derived from the chart class that you want. You'll need to either override `get_categories`, `get_dataset_labels` and `get_datasets`, or override `load`, where you can just call the functions you need to call to set up your chart:

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

Then in your view code, use this class instead:

    from .wildewidgets import TestChart

    class HomeView(TemplateView):
        template_name = "core/home.html"

        def get_context_data(self, **kwargs):
            kwargs['barchart'] = TestChart(width='500', height='400', thousands=True)
            return super().get_context_data(**kwargs)    

In your template, display the chart as before:

    {{barchart}}

### Histograms

Histograms are built slightly differently. You'll need to call the object's `build` function, with arguments for a list of values, and the number of bins you want. The histogram will utilize ajax if the build function is called in the `load` function:

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

## Scientific Charts and Graphs Usage

### Without Ajax

In your view code, import the AltairChart class, and the pandas and altair libraries (the pandas library and other requirements will be automatically installed when installing the altair library):

    import pandas as pd
    import altair as alt
    from wildewidgets import AltairChart

and define the chart in your view:

class AltairView(TemplateView):
    template_name = "core/altair.html"

    def get_context_data(self, **kwargs):
        data = pd.DataFrame({
            'a': list('CCCDDDEEE'),
            'b': [2, 7, 4, 1, 2, 6, 8, 4, 7]
            }
        )
        spec = alt.Chart(data).mark_point().encode(
            x='a',
            y='b'
        )
        chart = AltairChart(title='Scientific Proof')
        chart.set_data(spec)
        kwargs['chart'] = chart
        return super().get_context_data(**kwargs)

In your template, display the chart:

    {{chart}}

### With Ajax

Create a file called `wildewidgets.py` in your app directory if it doesn't exist already and create a new class derived from the AltairChart class. You'll need to either override the `load` method, where you'll define your altair chart:

    import pandas as pd
    import altair as alt
    from wildewidgets import AltairChart

    class SciChart(AltairChart):

    def load(self):
        data = pd.DataFrame({
            'a': list('CCCDDDEEE'),
            'b': [2, 7, 4, 1, 2, 6, 8, 4, 10]
            }
        )
        spec = alt.Chart(data).mark_point().encode(
            x='a',
            y='b'
        )
        self.set_data(spec)

Then in your view code, use this class instead:

    from .wildewidgets import SciChart

    class HomeView(TemplateView):
        template_name = "core/altair.html"

        def get_context_data(self, **kwargs):
            kwargs['scichart'] = SciChart()
            return super().get_context_data(**kwargs)    

In your template, display the chart:

    {{scichart}}

## Tables Usage

### Without Ajax

In your view code, import the DataTable:

    from wildewidgets import DataTable

and define the table in your view:

    class TableView(TemplateView):
        template_name = "core/tables.html"

        def get_context_data(self, **kwargs):
            table = DataTable()
            table.add_column('time')
            table.add_column('pressure')
            table.add_column('temperature')
            table.add_row(time=12, pressure=53, temperature=25)
            table.add_row(time=13, pressure=63, temperature=24)
            table.add_row(time=14, pressure=73, temperature=23)
            kwargs['table'] = table
            return super().get_context_data(**kwargs)

In your template, display the chart:

    {{table}}

### With Ajax

Create a file called `wildewidgets.py` in your app directory if it doesn't exist already and create a new class derived from the DataTable class. You'll need to provide a model, or override `get_initial_queryset`. Then add the fields that you want displayed in the table:

    from wildewidgets import DataTable

    class TestTable(DataTable):

        model = Measurement

        def __init__(self, *args, **kwargs):
            if not "table_id" in kwargs:
                kwargs["table_id"] = "data_measurement"
            super().__init__(*args, **kwargs)
            self.add_column('name')
            self.add_column('time', searchable=False)
            self.add_column('pressure')
            self.add_column('temperature')
            self.add_column('restricted', visible=False)
            self.add_column('open', sortable=False)

In your view code, use this class instead:

    from .wildewidgets import TestTable

    class TableView(TemplateView):
    template_name = "core/tables.html"

    def get_context_data(self, **kwargs):
        kwargs['table'] = TestTable()
        return super().get_context_data(**kwargs)

In your template, display the chart:

    {{table}}

## Business Charts Options

There are a number of available Charts:

* BarChart
* HorizontalBarChart
* StackedBarChart
* HorizontalStackedBarChart
* PieChart
* DoughnutChart
* Histogram
* HorizontalHistogram

There are a number of options you can set for a specific chart:

    width: chart width in pixels (default: 400)
    height: chart height in pixels (default: 400)
    title: title text (default: None)
    color: use color as opposed to grayscale (default: True)
    legend: whether or not to show the legend - True/False (default: False)
    legend-position: top, right, bottom, left (default: left)
    thousands: if set to true, numbers are abbreviated as in 1K 5M, ... (default: False)
    money: whether or not the value is money (default: False)
    url: a click on a segment of a chart will redirect to this URL, with parameters label and value

### Colors

You can also customize the colors by either overriding the class variable 'COLORS' or calling the member function set_colors. The format is a list of RGB tuples.

### Fonts

To customize the fonts globally, the available Django settings are:

    CHARTJS_FONT_FAMILY = "'Vaud', sans-serif"
    CHARTJS_TITLE_FONT_SIZE = '18'
    CHARTJS_TITLE_FONT_STYLE = 'normal'
    CHARTJS_TITLE_PADDING = '0'

## Scientific Charts Options

Most of the options of a scientific chart or graph are set in the Altair code, but there are a few that can be set here:

    width: chart width (default: 400px)
    height: chart height (default: 300px)
    title: title text (default: None)

## Table Options

There are a few options you can set for a table:

    title: title text (default: None)
    page_length: number of rows to initially display

You can add further options to particular columns when you call `add_column`:

    verbose_name: specify a name other then the field name capitalized (default: None)
    searchable: whether the column is searchable (default: True)
    sortable: whether the column is sortable (default: True)
    align: how the value is aligned (default: left)
    visible: whether the column is initially visible (default: True)

You can specify custom filters by field:

    class TestTable(DataTable):

        model = Measurement

        def __init__(self, *args, **kwargs):
            if not "table_id" in kwargs:
                kwargs["table_id"] = "data_measurement"
            super().__init__(*args, **kwargs)
            self.add_column('name')
            self.add_column('time', searchable=False)
            self.add_column('pressure')
            self.add_column('temperature')
            self.add_column('restricted', visible=False)
            self.add_column('open', sortable=False)

            filter = DataTableFilter()
            filter.add_choice("True", "True")
            filter.add_choice("False", "False")
            self.add_filter('restricted', filter)

            filter = DataTableFilter()
            filter.add_choice("True", "True")
            filter.add_choice("False", "False")
            self.add_filter('open', filter)

            filter = DataTableFilter()
            filter.add_choice("< 1000", "level_1000")
            filter.add_choice("1000-2000", "level_2000")
            filter.add_choice("2000-3000", "level_3000")
            self.add_filter('pressure', filter)

Generally, for these filters to work, you will have to override the default searching function for the corresponding field:

        def search_pressure_column(self, qs, column, value):
            if value=='level_1000':
                qs = qs.filter(pressure__lt=1000)    
            elif value=='level_2000':
                qs = qs.filter(pressure__lt=2000).filter(pressure__gte=1000)
            elif value=='level_3000':
                qs = qs.filter(pressure__lt=3000).filter(pressure__gte=2000)
            else:
                qs = qs.filter(pressure__contains=value)
            return qs

        def search_restricted_column(self, qs, column, value):
            test = value=='True'
            qs = qs.filter(restricted=test)
            return qs

        def search_open_column(self, qs, column, value):
            test = value=='True'
            qs = qs.filter(open=test)
            return qs

You can change the default display of a particular column by overriding the corresponding `render` method:

        def render_date_column(self, row, column):
            return row.date.strftime("%B %-d, %Y")

        def render_open_trip_column(self, row, column):
            if not row.completed:
                return '<span class="fas fa-calendar-times text-info pl-2"></span>'
            else:
                return ''

You can also add custom fields that are not part of the model, but are calculated, by overriding the corresponding `render` method:

        def render_overheated_column(self, row, column):
            if row.temperature > 1500:
                return "Overheated"
            return "Normal"

If you want to add a column that has a foreign key, rather than a value, include the printable attribute of the foreign key's model. For example, if you want a column to show a user's first_name, use:

    self.add_column('user__first_name', verbose_name='First Name')
