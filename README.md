# Django Wildewidgets

django-wildewidgets is a Django app to help make charts, tables, and UI widgets 
quickly and easily with libraries like Chartjs, Altair, and Datatables.

## Quick start

Install:

    pip install django-wildewidgets


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

For [ChartJS](https://www.chartjs.org/) (the regular business type charts), add the corresponding javascript file:

    <script src="https://cdn.jsdelivr.net/npm/chart.js@2.9.4/dist/Chart.min.js"></script> 

For [Altair](https://github.com/altair-viz/altair) (the scientific charts), use:

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

and define the chart:

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

Create a file called `wildewidgets.py` in your app directory and create a new class. You'll need to either override `get_categories`, `get_dataset_labels` and `get_datasets`, or override `load`, where you can just call the functions you need to call to set up your chart:

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




