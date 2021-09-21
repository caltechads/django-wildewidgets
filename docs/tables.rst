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

In your template, display the table::

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

In your template, display the table::

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

Filters
=======

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


Basic Model Table
=================

If you have a basic model and want a standard table layout, you can make a derived class of `BasicModelTable` and set some class variables.

Options
-------

There are some mandatory options, and some optional ones.

    model 
        (required) the Django model class

    fields
        (optional) list of model fields. If not included, `__all__` will be assumed. This can include fields from related objects in the form `related_field__field`.

    hidden
        (optional) list of model fields that are included in `fields`, but won't be displayed by default.

    verbose_names
        (optional) dictionary of verbose names with `field` as the key. By default, the model field's verbose name will be used.

    actions
        (optional) list of tuples of action buttons. If this exists, an Action column will be appended to the table, and buttons will be added for each tuple. The tuples are in the form `('Label', 'url-name', 'get (default)/post', 'bootstrap color class (default secondary)', 'id attribute (default id)')`.

    form_actions
        (optional) if you want the table to be a form that can act on the rows, include the form actions here in the form of a list of tuples that correspond to the value and label of the select options. If this exists, a column of checkboxes will be prepended to the table.

    form_url
        (optional) the form `action` url.

    page_length
        (optional) set the page length of the table.

    small
        (optional) use a table with thinner rows.

    buttons
        (optional) display the print buttons.

    striped
        (optional) use a table with striped rows.

As an example::

        from wildewidgets import BasicModelTable

        class TestTable(BasicModelTable):
            model = SpecialGroup
            fields = ['group', 'account__description', 'group_type', 'name', 'description', 'network_id']        
            hidden = ['name', 'network_id']
            verbose_names = {'account__description':'Account'}
            actions = [('Nag', 'core:nag', 'post')]
            form_actions = [('action1', 'Action 1'), ('action2', 'Action 2')]
            form_url = reverse_lazy('core:action_test')

If you have `form_actions`, you will need to use the wildewidgets templatetag to display the table, in order to have the csrf token included:

In your template, load the wildewidgets templatetag::

    {% load <your other tags> wildewidgets %}

Then display the table::

    {% wildewidgets table %}

You can also have a conditional action button that only shows up on rows that meet your criteria. To do this, you must override ``get_conditional_action_buttons``::

        def get_conditional_action_buttons(self, row):
            if condition:
                return self.get_action_button(row, 'Action', 'core:myaction')
            return ''

Table Form View Processing
--------------------------

To process the table form submissions, override `TableActionFormView`, and implement `process_form_action`::

        class ActionTestView(TableActionFormView):
            url = reverse_lazy('core:home')

            def process_form_action(self, action, items):    
                for item in items:
                    print(action, item)

The `action` will be the value passed as the first item of the tuple in the form_actions attribute. The `items` will be a list of ids corresponding to the objects listed in the rows that have their checkbox checked.
