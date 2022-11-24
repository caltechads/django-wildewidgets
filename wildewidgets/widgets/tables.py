from copy import copy
from functools import lru_cache
import random
import re

from django import template
from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils.html import escape

from wildewidgets.views import (JSONResponseView, WidgetInitKwargsMixin)

from .base import Widget

import logging
logger = logging.getLogger(__name__)


class DatatableMixin:
    model = None

    columns = []
    _columns = []               # internal cache for columns definition
    order_columns = []

    max_display_length = 100    # max limit of records returned, do not allow to kill our server by huge sets  of data
    pre_camel_case_notation = False  # datatables 1.10 changed query string parameter names
    none_string = ''
    escape_values = True        # if set to true then values returned by render_column will be escaped
    columns_data = []
    # is_data_list determines the type of results. If JavaScript passes data attribute that is not an integer, it
    # expects a dictionary with specific fields in the response, see:
    # https://datatables.net/reference/option/columns.data
    is_data_list = True

    FILTER_ISTARTSWITH = 'istartswith'
    FILTER_ICONTAINS = 'icontains'

    @property
    def _querydict(self):
        if self.request.method == 'POST':
            return self.request.POST
        else:
            return self.request.GET

    def get_filter_method(self):
        """
        Returns preferred filter method.
        """
        return self.FILTER_ISTARTSWITH

    def initialize(self, *args, **kwargs):
        """
        Determine which version of DataTables is being used - there are differences in parameters sent by
        DataTables < 1.10.x
        """
        if 'iSortingCols' in self._querydict:
            self.pre_camel_case_notation = True

    def get_order_columns(self):
        """
        Return list of columns used for ordering.

        By default returns self.order_columns but if these are not defined it tries to get columns from the request
        using the ``columns[i][name]`` attribute. This requires proper client side definition of columns, eg::

            columns: [
                {
                    name: 'username',
                    data: 'username',
                    orderable: true,
                },
                {
                    name: 'email',
                    data: 'email',
                    orderable: false
                }
            ]
        """
        if self.order_columns or self.pre_camel_case_notation:
            return self.order_columns

        # try to build list of order_columns using request data
        order_columns = []
        for column_def in self.columns_data:
            if column_def['name'] or not self.is_data_list:
                # if self.is_data_list is False then we have a column name in the 'data' attribute, otherwise
                # 'data' attribute is an integer with column index
                if column_def['orderable']:
                    if self.is_data_list:
                        order_columns.append(column_def['name'])
                    else:
                        order_columns.append(column_def.get('data'))
                else:
                    order_columns.append('')
            else:
                # fallback to columns
                order_columns = self._columns
                break

        self.order_columns = order_columns
        return order_columns

    def get_columns(self):
        """
        Returns the list of columns to be returned in the result set.

        By default returns self.columns but if these are not defined it tries to get columns from the request using the
        ``columns[i][data]`` or columns[i][name] attribute.  This requires proper client side definition of columns,
        e.g.::

            columns: [
                {
                    data: 'username'
                },
                {
                    data: 'email'
                }
            ]
        """
        if self.columns or self.pre_camel_case_notation:
            return self.columns

        columns = []
        for column_def in self.columns_data:
            if self.is_data_list:
                # if self.is_data_list is True then 'data' atribute is an integer - column index, so we
                # cannot use it as a column name, let's try 'name' attribute instead
                col_name = column_def['name']
            else:
                col_name = column_def['data']

            if col_name:
                columns.append(col_name)
            else:
                return self.columns

        return columns

    @staticmethod
    def _column_value(obj, key):
        """
        Returns the value from a queryset item.
        """
        if isinstance(obj, dict):
            return obj.get(key, None)

        return getattr(obj, key, None)

    def _render_column(self, row, column):
        """
        Renders a column on a row. column can be given in a module notation eg. ``document.invoice.type``
        """
        # try to find rightmost object
        obj = row
        parts = column.split('.')
        for part in parts[:-1]:
            if obj is None:
                break
            obj = getattr(obj, part)

        # try using get_OBJECT_display for choice fields
        if hasattr(obj, 'get_%s_display' % parts[-1]):
            value = getattr(obj, 'get_%s_display' % parts[-1])()
        else:
            value = self._column_value(obj, parts[-1])

        if value is None:
            value = self.none_string

        if self.escape_values:
            value = escape(value)

        return value

    def render_column(self, row, column):
        """
        Renders a column on a row. column can be given in a module notation eg. ``document.invoice.type``
        """
        value = self._render_column(row, column)
        # if value and hasattr(row, 'get_absolute_url'):
        #     return format_html('<a href="{}">{}</a>', row.get_absolute_url(), value)
        return value

    def ordering(self, qs):
        """
        Get parameters from the request and prepare order by clause.
        """

        # Number of columns that are used in sorting
        sorting_cols = 0
        if self.pre_camel_case_notation:
            try:
                sorting_cols = int(self._querydict.get('iSortingCols', 0))
            except ValueError:
                sorting_cols = 0
        else:
            sort_key = 'order[{0}][column]'.format(sorting_cols)
            while sort_key in self._querydict:
                sorting_cols += 1
                sort_key = 'order[{0}][column]'.format(sorting_cols)

        order = []
        order_columns = self.get_order_columns()

        for i in range(sorting_cols):
            # sorting column
            sort_dir = 'asc'
            try:
                if self.pre_camel_case_notation:
                    sort_col = int(self._querydict.get('iSortCol_{0}'.format(i)))
                    # sorting order
                    sort_dir = self._querydict.get('sSortDir_{0}'.format(i))
                else:
                    sort_col = int(self._querydict.get('order[{0}][column]'.format(i)))
                    # sorting order
                    sort_dir = self._querydict.get('order[{0}][dir]'.format(i))
            except ValueError:
                sort_col = 0

            sdir = '-' if sort_dir == 'desc' else ''
            sortcol = order_columns[sort_col]
            if not sortcol:
                continue

            if isinstance(sortcol, list):
                for sc in sortcol:
                    order.append('{0}{1}'.format(sdir, sc.replace('.', '__')))
            else:
                order.append('{0}{1}'.format(sdir, sortcol.replace('.', '__')))

        if order:
            return qs.order_by(*order)
        return qs

    def paging(self, qs):
        if self.pre_camel_case_notation:
            limit = min(int(self._querydict.get('iDisplayLength', 10)), self.max_display_length)
            start = int(self._querydict.get('iDisplayStart', 0))
        else:
            limit = min(int(self._querydict.get('length', 10)), self.max_display_length)
            start = int(self._querydict.get('start', 0))

        # if pagination is disabled ("paging": false)
        if limit == -1:
            return qs

        offset = start + limit

        return qs[start:offset]

    def get_initial_queryset(self):
        if not self.model:
            raise NotImplementedError("Need to provide a model or implement get_initial_queryset!")
        return self.model.objects.all()

    def extract_datatables_column_data(self):
        """
        Helper method to extract columns data from request as passed by Datatables 1.10+.
        """
        request_dict = self._querydict
        col_data = []
        if not self.pre_camel_case_notation:
            counter = 0
            data_name_key = 'columns[{0}][name]'.format(counter)
            while data_name_key in request_dict:
                searchable = request_dict.get('columns[{0}][searchable]'.format(counter)) == 'true'
                orderable = request_dict.get('columns[{0}][orderable]'.format(counter)) == 'true'

                col_data.append(
                    {
                        'name': request_dict.get(data_name_key),
                        'data': request_dict.get('columns[{0}][data]'.format(counter)),
                        'searchable': searchable,
                        'orderable': orderable,
                        'search.value': request_dict.get('columns[{0}][search][value]'.format(counter)),
                        'search.regex': request_dict.get('columns[{0}][search][regex]'.format(counter))
                    }
                )
                counter += 1
                data_name_key = 'columns[{0}][name]'.format(counter)
        return col_data

    def prepare_results(self, qs):
        data = []
        for item in qs:
            if self.is_data_list:
                data.append([self.render_column(item, column) for column in self._columns])
            else:
                row = {col_data['data']: self.render_column(item, col_data['data']) for col_data in self.columns_data}
                data.append(row)

        return data

    def handle_exception(self, e):
        logger.exception(str(e))
        raise e

    def get_context_data(self, *args, **kwargs):
        try:
            self.initialize(*args, **kwargs)

            # prepare columns data (for DataTables 1.10+)
            self.columns_data = self.extract_datatables_column_data()

            # determine the response type based on the 'data' field passed from JavaScript
            # https://datatables.net/reference/option/columns.data
            # col['data'] can be an integer (return list) or string (return dictionary)
            # we only check for the first column definition here as there is no way to return list and dictionary
            # at once
            self.is_data_list = True
            if self.columns_data:
                self.is_data_list = False
                try:
                    int(self.columns_data[0]['data'])
                    self.is_data_list = True
                except ValueError:
                    pass

            # prepare list of columns to be returned
            self._columns = self.get_columns()

            # prepare initial queryset
            qs = self.get_initial_queryset()

            # store the total number of records (before filtering)
            total_records = qs.count()

            # apply filters
            qs = self.filter_queryset(qs)

            # number of records after filtering
            total_display_records = qs.count()

            # apply ordering
            qs = self.ordering(qs)

            # apply pagintion
            qs = self.paging(qs)

            # prepare output data
            if self.pre_camel_case_notation:
                aaData = self.prepare_results(qs)

                ret = {'sEcho': int(self._querydict.get('sEcho', 0)),
                       'iTotalRecords': total_records,
                       'iTotalDisplayRecords': total_display_records,
                       'aaData': aaData
                       }
            else:
                data = self.prepare_results(qs)

                ret = {'draw': int(self._querydict.get('draw', 0)),
                       'recordsTotal': total_records,
                       'recordsFiltered': total_display_records,
                       'data': data
                       }
            return ret
        except Exception as e:
            return self.handle_exception(e)


class BaseDatatableView(DatatableMixin, JSONResponseView):
    pass


class DatatableAJAXView(BaseDatatableView):
    """
    This is a JSON view that a DataTables.js table can hit as for its AJAX queries.
    """

    def columns(self, querydict):
        """
        Parse the request we got from the DataTables AJAX request (``querydict``) from a list of strings to a more
        useful nested dict.  We'll use this to more readily figure out what we need to be doing.

        A single column's data in the querystring we got from datatables looks like::

            {
                'columns[4][data]': 'employee_number',
                'columns[4][name]': '',
                'columns[4][orderable]': 'true',
                'columns[4][search][regex]': 'false',
                'columns[4][search][value]': '',
                'columns[4][searchable]': 'true'
            }

        Turn all such data into a dict that looks like::

            {
                'employee_number': {
                    'column_number': 4,
                    'data': 'employee_number',
                    'name': '',
                    'orderable': True,
                    'search': {
                        'regex': False,
                        'value': ''
                    },
                    'searchable': True
                }
            }

        :param querydict: dict of all key, value pairs from the ajax request.
        :type querydict: dict

        :rtype: dict
        """
        by_number = {}
        for key, value in querydict.items():
            if value == 'true':
                value = True
            elif value == 'false':
                value = False
            if key.startswith('columns'):
                parts = key.split('[')
                column_number = parts[1][:-1]
                column_attribute = parts[2][:-1]
                if column_number not in by_number:
                    by_number[column_number] = {
                        'column_number': int(column_number)
                    }
                if len(parts) == 4:
                    if column_attribute not in by_number[column_number]:
                        by_number[column_number][column_attribute] = {parts[3][:-1]: value}
                    else:
                        by_number[column_number][column_attribute][parts[3][:-1]] = value
                else:
                    by_number[column_number][column_attribute] = value
        # Now make the real lookup be by column name
        by_name = {}
        for key in by_number:
            # 'data' is the column name
            by_name[by_number[key]['data']] = by_number[key]
        return by_name

    @lru_cache(maxsize=4)
    def searchable_columns(self):
        """
        Return the list of all column names from out DataTable that are marked as "searchable"

        :rtype: list of strings
        """
        return [key for key, value in self.columns(self._querydict).items() if value['searchable']]

    def column_specific_searches(self):
        """
        Look through the request data we got from the DataTable AJAX request for any single-column
        searches.  These will look like ``column[$number][search][value]`` in the request.

        :rtype: list of 2-tuples (str, str): (column name, search string)
        """
        return [
            (key, value['search']['value'])
            for key, value in self.columns(self._querydict).items()
            if value['search']['value']
        ]

    def single_column_filter(self, qs, column, value):
        """
        Filter our queryset by a single column.  Columns will be searched by ``__icontains``.

        This gets executed when someone runs a search on a single DataTables.js column::

            data_table.column($number).search($search_string);

        If you want to implement a different search filter for a particular column, add a
        ``search_COLUMN_column(self, qs, column, value)`` method that returns a QuerySet
        to your subclass and that will be called instead.  Example::

            def search_foobar_column(self, qs, column, value):
                if value == 'something':
                    qs = qs.filter(foobar__attribute=True)
                elif value == 'other_thing':
                    qs = qs.filter(foobar__other_attribute=False)
                return qs

        :param qs: the Django QuerySet
        :type qs: QuerySet

        :param column : the dataTables data attribute for the column we're interested in
        :type column: str

        :param value: the search string
        :type value: str

        :rtype: QuerySet
        """
        attr_name = 'filter_{}_column'.format(column)
        if hasattr(self, attr_name):
            qs = getattr(self, attr_name)(qs, column, value)
        elif column in self.searchable_columns():
            kwarg_name = '{}__icontains'.format(column)
            qs = qs.filter(**{kwarg_name: value})
        return qs

    def search_query(self, qs, value):
        # 2020-08-05 rrollins TODO: This is very likely wrong. It doesn't use qs at all, and doesn't return a QuerySet.
        """
        Return an ORed Q() object that will search the searchable fields for ``value``

        :param qs: the Django QuerySet
        :type qs: QuerySet

        :param value: the search string
        :type value: str

        :rtype: Q() object
        """
        query = None
        for column in self.searchable_columns():
            attr_name = 'search_{}_column'.format(column)
            if hasattr(self, attr_name):
                q = getattr(self, attr_name)(column, value)
            else:
                kwarg_name = '{}__icontains'.format(column)
                q = Q(**{kwarg_name: value})
            query = query | q if query else q
        return query

    def search(self, qs, value):
        """
        Filter our queryset across all of our searchable columns for ``value``.

        This gets executed when someone runs a search over the whole DataTables.js table::

            data_table.search($search_string);

        This is what happens when the user uses the Search input on the DataTable.

        :param qs: the Django QuerySet
        :type qs: QuerySet

        :param value: the search string
        :type value: str

        :rtype: QuerySet
        """
        query = self.search_query(qs, value)
        qs = qs.filter(query).distinct()
        return qs

    def filter_queryset(self, qs):
        """
        We're overriding the default filter_queryset(method) here so we can implement proper searches on our
        pseudo-columns "responded" and "disabled", and do column specific searches, as well as doing
        general searches across our regular CharField columns.
        """
        column_searches = self.column_specific_searches()
        if column_searches:
            for column, value in column_searches:
                qs = self.single_column_filter(qs, column, value)
        value = self.request.GET.get('search[value]', None)
        if value:
            qs = self.search(qs, value)
        return qs

    def _render_column(self, row, column):
        """
        When defining our DataTable config, we declare DataTable columns that access columns of models of foreign keys
        on our model with ``__`` notation.  Convert the ``__`` to ``.`` before trying to render the data so
        that things will work correctly.


        :param row: A Django model instance
        :param column: the name of the column to render

        :rtype: string
        """
        column = re.sub('__', '.', column)
        return super()._render_column(row, column)

    def render_column(self, row, column):
        """
        Return the data to add to the DataTable for column ``column`` of the table row corresponding to
        the model object ``row``.

        If you want to implement special rendering a particular column (for instance to display something about an
        object that doesn't map directly to a model column), add a ``render_COLUMN_column(self, row, column)`` method
        that returns a string to your subclass and that will be called instead.  Example::

            def render_foobar_column(self, row, column):
                return 'some data'

        :param row: A Django model instance
        :param column: the name of the column to render

        :rtype: string
        """
        attr_name = 'render_{}_column'.format(column)
        if hasattr(self, attr_name):
            return getattr(self, attr_name)(row, column)
        else:
            return super().render_column(row, column)


class DataTableColumn:

    def __init__(self, field, verbose_name=None, searchable=False, sortable=False, align='left',
                 head_align='left', visible=True, wrap=True):
        self.field = field
        if verbose_name:
            self.verbose_name = verbose_name
        else:
            self.verbose_name = field.capitalize()
        self.searchable = searchable
        self.sortable = sortable
        self.align = align
        self.head_align = head_align
        self.visible = visible
        self.wrap = wrap


class DataTableFilter:

    def __init__(self, header=None):
        self.header = header
        self.choices = [('Any', '')]

    def add_choice(self, label, value):
        self.choices.append((label, value))


class DataTableStyler:

    def __init__(self, is_row, test_cell, cell_value, css_class, target_cell=None):
        self.is_row = is_row
        self.test_cell = test_cell
        self.cell_value = cell_value
        self.css_class = css_class
        self.target_cell = target_cell
        self.test_index = 0
        self.target_index = 0


class DataTableForm:

    def __init__(self, table):
        if table.has_form_actions():
            self.is_visible = True
        else:
            self.is_visible = False
        self.actions = table.get_form_actions()
        self.url = table.form_url


class DataTable(Widget, WidgetInitKwargsMixin, DatatableAJAXView):
    template_file = 'wildewidgets/table.html'
    actions = False
    form_actions = None
    form_url = ''
    hide_controls = False
    table_id = None
    default_action_button_label = 'View'
    default_action_button_color_class = 'secondary'
    sort_ascending = True
    action_button_size = 'normal'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.options = {
            'width': kwargs.get('width', '100%'),
            'height': kwargs.get('height', None),
            "title": kwargs.get('title', None),
            "searchable": kwargs.get('searchable', True),
            "paging": kwargs.get('paging', True),
            "page_length": kwargs.get('page_length', None),
            "small": kwargs.get('small', False),
            "buttons": kwargs.get('buttons', False),
            "striped": kwargs.get('striped', False),
            "hide_controls": self.hide_controls
        }
        self.table_id = kwargs.get('table_id', self.table_id)
        self.async_if_empty = kwargs.get('async', True)
        self.column_fields = {}
        self.column_filters = {}
        self.column_styles = []
        self.data = kwargs.get('data', [])
        self._form_actions = copy(self.form_actions)
        if self.form_actions:
            self.column_fields['checkbox'] = DataTableColumn(
                field='checkbox',
                verbose_name=' ',
                searchable=False,
                sortable=False
            )
        self.sort_ascending = kwargs.get('sort_ascending', self.sort_ascending)
        self.action_button_size = kwargs.get('action_button_size', self.action_button_size)
        if not self.action_button_size == 'normal':
            self.action_button_size_class = f"btn-{self.action_button_size}"
        else:
            self.action_button_size_class = ''

    def has_form_actions(self):
        return not self._form_actions == None

    def get_form_actions(self):
        return self._form_actions

    def add_form_action(self, action):
        self._form_actions.append(action)

    def get_order_columnsx(self):
        cols = []
        for field, col in self.column_fields.items():
            if col.sortable:
                cols.append(field)
        return cols

    def add_column(self, field, verbose_name=None, searchable=True, sortable=True, align='left',
                   head_align='left', visible=True, wrap=True):
        self.column_fields[field] = DataTableColumn(
            field=field,
            verbose_name=verbose_name,
            searchable=searchable,
            sortable=sortable,
            align=align,
            head_align=head_align,
            visible=visible,
            wrap=wrap
        )

    def add_filter(self, field, filter):
        self.column_filters[field] = filter

    def remove_filter(self, field):
        del self.column_filters[field]

    def add_styler(self, styler):
        styler.test_index = list(self.column_fields.keys()).index(styler.test_cell)
        if styler.target_cell:
            styler.target_index = list(self.column_fields.keys()).index(styler.target_cell)
        self.column_styles.append(styler)

    def build_context(self):
        return {'rows': self.data}
        # return {'rows': self.prepare_results(self.data)}

    def get_content(self, **kwargs):
        if self.actions:
            self.add_column(field='actions', searchable=False, sortable=False)
        has_filters = False
        filters = []
        for key, item in self.column_fields.items():
            if key in self.column_filters:
                filters.append((item, self.column_filters[key]))
                has_filters = True
            else:
                filters.append(None)
        if self.table_id:
            table_id = self.table_id
        else:
            table_id = random.randrange(0, 1000)
        template_file = self.template_file
        if self.data or not self.async_if_empty:
            context = self.build_context()
            context['async'] = False
        else:
            context = {"async": True}
        html_template = template.loader.get_template(template_file)
        context['header'] = self.column_fields
        context['has_form_actions'] = self.has_form_actions()
        if self.actions:
            context['has_actions'] = True
            context['action_column'] = len(self.column_fields) - 1
        else:
            context['has_actions'] = False        
        context['filters'] = filters
        context['stylers'] = self.column_styles
        context['has_filters'] = has_filters
        context['options'] = self.options
        context['name'] = f"datatable_table_{table_id}"
        context['sort_ascending'] = self.sort_ascending
        context["tableclass"] = self.__class__.__name__
        if not self.data:
            context["extra_data"] = self.get_encoded_extra_data()
        context["form"] = DataTableForm(self)
        if 'csrf_token' in kwargs:
            context["csrf_token"] = kwargs['csrf_token']
        content = html_template.render(context)
        return content

    def __str__(self):
        return self.get_content()

    def add_row(self, **kwargs):
        row = []
        for field in self.column_fields.keys():
            if field in kwargs:
                row.append(kwargs[field])
            else:
                row.append('')
        self.data.append(row)

    def get_action_button(self, row, label, url_name, method='get', color_class='secondary', attr='id',
                          js_function_name=None):
        if url_name:
            base = reverse_lazy(url_name)
            if method == 'get':
                url = f"{base}?{attr}={row.id}"
            else:
                url = base
        else:
            url = "javascript:void(0)"
        return self.get_action_button_with_url(row, label, url, method, color_class, attr, js_function_name)

    def get_action_button_url_extra_attributes(self, row):
        return ""

    def get_action_button_with_url(self, row, label, url, method='get', color_class='secondary', attr='id',
                                   js_function_name=None):
        url_extra = self.get_action_button_url_extra_attributes(row)
        if url_extra:
            url = f"{url}&{url_extra}"                                   
        if method == 'get':
            if js_function_name:
                link_extra = f"onclick='{js_function_name}({row.id});'"
            else:
                link_extra = ""
            return f"<a href='{url}' class='btn btn-{color_class} {self.action_button_size_class} me-2' {link_extra}>{label}</a>"
        token_input = f'<input type="hidden" name="csrfmiddlewaretoken" value="{self.csrf_token}">'
        id_input = f'<input type="hidden" name="{attr}" value="{row.id}">'
        button = f'<input type=submit value="{label}" class="btn btn-{color_class} {self.action_button_size_class} me-2">'
        form = f"<form class='form form-inline' action={url} method='post'>{token_input}{id_input}{button}</form>"
        return form

    def get_conditional_action_buttons(self, row):
        return ''

    def render_actions_column(self, row, column):
        response = "<div class='d-flex flex-row justify-content-end'>"
        if hasattr(row, 'get_absolute_url'):
            url = row.get_absolute_url()
            view_button = self.get_action_button_with_url(row, self.default_action_button_label, url, color_class=self.default_action_button_color_class)
            response += view_button
        if not type(self.actions) == bool:
            for action in self.actions:
                if not len(action) > 1:
                    continue
                label = action[0]
                url_name = action[1]
                if len(action) > 2:
                    method = action[2]
                else:
                    method = 'get'
                if len(action) > 3:
                    color_class = action[3]
                else:
                    color_class = 'secondary'
                if len(action) > 4:
                    attr = action[4]
                else:
                    attr = 'id'
                if len(action) > 5:
                    js_function_name = action[5]
                else:
                    js_function_name = ''
                response += self.get_action_button(row, label, url_name, method, color_class, attr, js_function_name)
        response += self.get_conditional_action_buttons(row)
        response += "</div>"
        return response

    def render_checkbox_column(self, row, column):
        return f"<input type='checkbox' name='checkbox' value='{row.id}'>"


class BasicModelTable(DataTable):
    fields = None
    hidden = []
    verbose_names = {}
    page_length = None
    small = None
    buttons = None
    striped = None
    unsortable = []
    unsearchable = []
    field_types = {}
    alignment = {}
    bool_icons = {}

    def __init__(self, *args, **kwargs):
        for field in ['page_length', 'small', 'buttons', 'striped']:
            value = getattr(self, field, None)
            if value:
                kwargs[field] = value
        super().__init__(*args, **kwargs)

        self.model_fields = {}
        self.related_fields = {}
        self.field_names = []
        for field in self.model._meta.get_fields():
            if field.name == 'id':
                continue
            self.model_fields[field.name] = field
            self.field_names.append(field.name)

        for field_name in self.fields:
            if field_name not in self.model_fields:
                field = self.get_related_field(self.model, field_name)
                if field:
                    self.related_fields[field_name] = field

        if not self.fields or self.fields == '__all__':
            self.load_all_fields()
        else:
            for field_name in self.fields:
                self.load_field(field_name)

    def get_related_model(self, current_model, field_name):
        field = current_model._meta.get_field(field_name)
        return field.related_model

    def get_related_field(self, current_model, name):
        name_fields = name.split('__')
        if len(name_fields) == 1:
            return None
        for field in name_fields[:-1]:
            current_model = self.get_related_model(current_model, field)
        if current_model:
            try:
                final_field = current_model._meta.get_field(name_fields[-1])
            except FieldDoesNotExist:
                final_field = None
        else:
            final_field = None
        return final_field

    def get_field(self, field_name):
        if field_name in self.model_fields:
            field = self.model_fields[field_name]
        elif field_name in self.related_fields:
            field = self.related_fields[field_name]
        else:
            field = None
        return field

    def set_standard_column_attributes(self, field_name, kwargs):
        if field_name in self.hidden:
            kwargs['visible'] = False
        if field_name in self.unsearchable:
            kwargs['searchable'] = False
        if field_name in self.unsortable:
            kwargs['sortable'] = False
        if field_name in self.alignment:
            kwargs['align'] = self.alignment[field_name]
        else:
            field = self.get_field(field_name)
            if isinstance(field, (models.TextField, models.CharField, models.DateField, models.DateTimeField)):
                kwargs['align'] = 'left'
            else:
                kwargs['align'] = 'right'

    def load_field(self, field_name):
        if field_name in self.model_fields:
            field = self.model_fields[field_name]
            verbose_name = field.name.replace('_', ' ')
            kwargs = {}
            if field_name in self.verbose_names:
                kwargs['verbose_name'] = self.verbose_names[field_name]
            elif hasattr(field, 'verbose_name'):
                if verbose_name == field.verbose_name:
                    kwargs['verbose_name'] = verbose_name.capitalize()
                else:
                    kwargs['verbose_name'] = field.verbose_name
            self.set_standard_column_attributes(field_name, kwargs)
            self.add_column(field_name, **kwargs)
        else:
            kwargs = {}
            if field_name in self.verbose_names:
                verbose_name = self.verbose_names[field_name]
            else:
                verbose_name = field_name.replace('_', ' ').replace('__', ' ').capitalize()
            kwargs['verbose_name'] = verbose_name
            self.set_standard_column_attributes(field_name, kwargs)
            self.add_column(field_name, **kwargs)

    def load_all_fields(self):
        for field_name in self.field_names:
            self.load_field(field_name)

    def render_currency_type_column(self, value):
        return f"${value}"

    def render_bool_type_column(self, value):
        if value == "True":
            return "<i class='bi-check-lg text-success'><span style='display:none'>True</span></i>"
        return ""

    def render_bool_icon_column(self, value, icon_data):
        if len(icon_data) == 0:
            return value
        if value == "True":
            return f"<i class='bi-{icon_data[0][0]} {icon_data[0][1]}'><span style='display:none'>True</span></i>"
        if len(icon_data) > 1:
            return f"<i class='bi-{icon_data[1][0]} {icon_data[1][1]}'><span style='display:none'>False</span></i>"
        return ""

    def render_datetime_type_column(self, value):
        datetime_format = "%m/%d/%Y %H:%M"
        if hasattr(settings, 'WILDEWIDGETS_DATETIME_FORMAT'):
            datetime_format = settings.WILDEWIDGETS_DATETIME_FORMAT
        if value:
            return value.strftime(datetime_format)
        return ""

    def render_date_type_column(self, value):
        date_format = "%m/%d/%Y"
        if hasattr(settings, 'WILDEWIDGETS_DATE_FORMAT'):
            date_format = settings.WILDEWIDGETS_DATE_FORMAT
        if value:
            return value.strftime(date_format)
        return ""

    def render_column(self, row, column):
        value = super().render_column(row, column)
        if column in self.model_fields:
            field = self.model_fields[column]
        elif column in self.related_fields:
            field = self.related_fields[column]
        else:
            field = None
        if column in self.field_types:
            field_type = self.field_types[column]
            attr_name = f"render_{field_type}_type_column"
            if hasattr(self, attr_name):
                if attr_name in ['date', 'datetime']:
                    value = getattr(row, column)
                return getattr(self, attr_name)(value)
        elif isinstance(field, models.DateTimeField):
            return self.render_datetime_type_column(getattr(row, column))
        elif isinstance(field, models.DateField):
            return self.render_date_type_column(getattr(row, column))
        elif column in self.bool_icons:
            return self.render_bool_icon_column(value, self.bool_icons[column])
        return value
