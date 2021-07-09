******
Tables
******

Tables make it easy to make tables using the `DataTables <https://github.com/DataTables/DataTables>`_ library.

Usage
=====

Without Ajax
------------

In your view code, import ``DataTable``::

    from wildewidgets import DataTable

and define the table in your view::

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

In your template, display the chart::

    {{table}}

With Ajax
---------

Create a file called ``wildewidgets.py`` in your app directory if it doesn't exist already and create a new class derived from the ``DataTable`` class. You'll need to provide a model, or override ``get_initial_queryset``. Then add the fields that you want displayed in the table::

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

In your view code, use this class instead::

    from .wildewidgets import TestTable

    class TableView(TemplateView):
        template_name = "core/tables.html"

        def get_context_data(self, **kwargs):
            kwargs['table'] = TestTable()
            return super().get_context_data(**kwargs)

In your template, display the chart::

    {{table}}

Options
=======

There are a few options you can set for a table::

    title: title text (default: None)
    paging: whether or not to allow paging
    page_length: number of rows to initially display
    small: reduced row height
    buttons: whether or not to show export buttons

You can add further options to particular columns when you call ``add_column``::

    verbose_name: specify a name other then the field name capitalized (default: None)
    searchable: whether the column is searchable (default: True)
    sortable: whether the column is sortable (default: True)
    align: how the value is aligned (default: left)
    visible: whether the column is initially visible (default: True)

You can specify custom filters by field::

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

Generally, for these filters to work, you will have to override the default searching function for the corresponding field::

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

You can change the default display of a particular column by overriding the corresponding ``render`` method::

        def render_date_column(self, row, column):
            return row.date.strftime("%B %-d, %Y")

        def render_open_trip_column(self, row, column):
            if not row.completed:
                return '<span class="fas fa-calendar-times text-info pl-2"></span>'
            else:
                return ''

You can also add custom fields that are not part of the model, but are calculated, by overriding the corresponding ``render`` method::

        def render_overheated_column(self, row, column):
            if row.temperature > 1500:
                return "Overheated"
            return "Normal"

If you want to add a column that has a foreign key, rather than a value, include the printable attribute of the foreign key's model. For example, if you want a column to show a user's first_name, use::

    self.add_column('user__first_name', verbose_name='First Name')

