```
     _ _                                     _ _     _               _     _            _       
    | (_)                                   (_) |   | |             (_)   | |          | |      
  __| |_  __ _ _ __   __ _  ___ _____      ___| | __| | _____      ___  __| | __ _  ___| |_ ___ 
 / _` | |/ _` | '_ \ / _` |/ _ \___\ \ /\ / / | |/ _` |/ _ \ \ /\ / / |/ _` |/ _` |/ _ \ __/ __|
| (_| | | (_| | | | | (_| | (_) |   \ V  V /| | | (_| |  __/\ V  V /| | (_| | (_| |  __/ |_\__ \
 \__,_| |\__,_|_| |_|\__, |\___/     \_/\_/ |_|_|\__,_|\___| \_/\_/ |_|\__,_|\__, |\___|\__|___/
     _/ |             __/ |                                                   __/ |             
    |__/             |___/                                                   |___/              
```

`django-wildewidgets` is a Django design library providing several tools for building
full-featured, widget-based web applications with a standard, consistent design, based 
on Bootstrap.

## Quick start

Install:

    pip install django-wildewidgets

If you plan on using [Altair charts](https://github.com/altair-viz/altair), run:

    pip install altair

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

First, add this to your `<head>`:

    <link rel="stylesheet" href="{% static 'wildewidgets/css/wildewidgets.css' %}"> 

For [ChartJS](https://www.chartjs.org/) (regular business type charts), add the corresponding javascript file:

    <script src="https://cdn.jsdelivr.net/npm/chart.js@2.9.4/dist/Chart.min.js"></script> 

For [Altair](https://github.com/altair-viz/altair) (scientific charts), use:

    <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
    <script src="https://cdn.jsdelivr.net/npm/vega-lite@4"></script>
    <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>  

For [DataTables](https://github.com/DataTables/DataTables), use:

    <script src="https://cdn.datatables.net/1.10.21/js/jquery.dataTables.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.8.4/moment.min.js"></script>
    <script src="https://cdn.datatables.net/plug-ins/1.10.21/sorting/datetime-moment.js"></script>

and:

    <link href="https://cdn.datatables.net/1.10.21/css/jquery.dataTables.min.css" rel="stylesheet" />

and, if using [Tabler](https://tabler.io), include:

    <link rel="stylesheet" href="{% static 'css/table_extra.css' %}"> 

For [ApexCharts](https://apexcharts.com), use:

    <script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>

If you plan on using CodeWidget, you'll need to include the following to get syntax highlighting:

    <link rel="stylesheet" href="{% static 'css/highlighting.css' %}"> 

## Documentation

[django-wildewidgets.readthedocs.io](http://django-wildewidgets.readthedocs.io/) is the full
reference for django-wildewidgets.
