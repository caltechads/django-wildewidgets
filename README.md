# Django Wildewidgets

django-wildewidgets is a Django app to help make charts, tables, and UI widgets 
quickly and easily with libraries like Chartjs, Altair, and Datatables.

Quick start
-----------

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
