************
Installation
************

django-wildewidgets is a Django library designed to help you make charts, graphs, tables, and UI widgets 
quickly and easily with libraries like Chartjs, Altair, and Datatables.

Quick start
===========

Install with pip
----------------

::

    pip install django-wildewidgets

If you plan on using `Altair charts <https://github.com/altair-viz/altair>`_, run::

    pip install altair

Configure
---------

Add "wildewidgets" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'wildewidgets',
    ]

Include the wildewidgets URLconf in your project urls.py like this::

    from wildewidgets import WildewidgetDispatch

    urlpatterns = [
        ...
        path('<urlbasepath>/wildewidgets_json', WildewidgetDispatch.as_view(), name='wildewidgets_json'),
    ]


Add the appropriate resources to your template files.

For `ChartJS <https://www.chartjs.org/>`_ (regular business type charts), add the corresponding javascript file::

    <script src="https://cdn.jsdelivr.net/npm/chart.js@2.9.4/dist/Chart.min.js"></script> 

For `Altair <https://github.com/altair-viz/altair>`_ (scientific charts), use::

    <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
    <script src="https://cdn.jsdelivr.net/npm/vega-lite@4"></script>
    <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>  

And for `DataTables <https://github.com/DataTables/DataTables>`_, use::

    <script src="https://cdn.datatables.net/1.10.21/js/jquery.dataTables.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.8.4/moment.min.js"></script>
    <script src="https://cdn.datatables.net/plug-ins/1.10.21/sorting/datetime-moment.js"></script>

and::

    <link href="https://cdn.datatables.net/1.10.21/css/jquery.dataTables.min.css" rel="stylesheet" />

If you want to add the export buttons to a DataTable, also add::

    <script type="text/javascript" src="https://cdn.datatables.net/autofill/2.3.5/js/dataTables.autoFill.min.js"></script>
    <script type="text/javascript" src="https://cdn.datatables.net/buttons/1.6.5/js/dataTables.buttons.min.js"></script>
    <script type="text/javascript" src="https://cdn.datatables.net/buttons/1.6.5/js/buttons.html5.min.js"></script>
    <script type="text/javascript" src="https://cdn.datatables.net/buttons/1.6.5/js/buttons.print.min.js"></script>
    <script type="text/javascript" src="{% static 'js/vendor/jszip.min.js' %}"></script>
    <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.70/pdfmake.min.js"></script>
    <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.70/vfs_fonts.min.js"></script>
    