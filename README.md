# Django Wildewidgets

django-wildewidgets is a Django library designed to help you make charts, graphs, tables, and UI widgets 
quickly and easily with libraries like Chartjs, Altair, and Datatables.

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

### Without Ajax (the data will load before the page has been loaded)

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

### With Ajax (the data will load after the page has been loaded)

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

## Scientific Charts and Graphs

### Without Ajax

In your view code, import the AltairChart class, and the pandas and altair libraries (the pandas library and other requirements will be automatically installed when installing the altair library):

    import pandas as pd
    import altair as alt
    from cheetahcharts import AltairChart

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
