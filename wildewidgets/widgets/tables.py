from copy import copy, deepcopy
import datetime
from functools import lru_cache
import logging
import random
import re
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from django import template
from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.urls import reverse
from django.db.models import Q
from django.utils.html import escape

from wildewidgets.views import (JSONResponseView, WidgetInitKwargsMixin)

from .base import Widget

logger = logging.getLogger(__name__)


class DatatableMixin:

    model: Optional[Type[models.Model]] = None

    columns = []
    #: internal cache for columns definition
    _columns = []
    order_columns = []

    #: The max number of of records that will be returned, so that we can protect our
    #: our server from rendering huge amounts of data
    max_display_length: int = 100
    # datatables 1.10 changed query string parameter names
    pre_camel_case_notation: bool = False
    none_string: str = ''
    # If set to ``True`` then values returned by :py:meth:`render_column`` will be escaped
    escape_values: bool = True
    columns_data = []
    #: This determines the type of results. If the AJAX call passes us a data attribute
    #: that is not an integer, it expects a dictionary with specific fields in
    #: the response, see: `dataTables columns.data
    #: <https://datatables.net/reference/option/columns.data>`_
    is_data_list: bool = True

    FILTER_ISTARTSWITH: str = 'istartswith'
    FILTER_ICONTAINS: str = 'icontains'

    @property
    def _querydict(self):
        if self.request.method == 'POST':
            return self.request.POST
        else:
            return self.request.GET

    def get_filter_method(self) -> str:
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

    def get_order_columns(self) -> List[str]:
        """
        Return list of columns used for ordering.

        By default returns :py:attr`order_columns` but if these are not defined it
        tries to get columns from the request using the ``columns[i][name]``
        attribute. This requires proper client side definition of columns, eg::

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

        By default returns :py:attr:`columns` but if these are not defined it tries to
        get columns from the request using the ``columns[i][data]`` or
        columns[i][name] attribute.  This requires proper client side definition
        of columns, e.g.::

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
                # if self.is_data_list is True then 'data' atribute is an
                # integer - column index, so we cannot use it as a column name,
                # let's try 'name' attribute instead
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

    def _render_column(self, row: Any, column: str) -> str:
        """
        Renders a column on a row. column can be given in a module notation eg.
        ``document.invoice.type``
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

    def render_column(self, row: Any, column: str) -> str:
        """
        Renders a column on a row. column can be given in a module notation eg.
        ``document.invoice.type``
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
        except Exception as e:  # pylint: disable=broad-except
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
        for key, value in by_number.items():
            # 'data' is the column name
            by_name[by_number[key]['data']] = value
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
        self.choices: List[Tuple[str, str]] = [('Any', '')]

    def add_choice(self, label: str, value: str) -> None:
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
            self.is_visible: bool = True
        else:
            self.is_visible = False
        self.actions = table.get_form_actions()
        self.url = table.form_url


class ActionsButtonsBySpecMixin:
    """
    This is a mixin class for :py:class:`DataTable` classes that allows you to specify
    buttons that will appear per row in an "Actions" column, rightmost of all columns.

    If :py:attr:`actions` is ``True``, and a row object has an attribute or
    method named ``get_absolute_url``,  render a single button named
    :py:attr:`default_action_button_label` that when clicked takes the user
    to that URL.

    Otherwise, :py:attr:`actions` should be a iterable of tuples or lists of
    the following structures::

        (label, Django URL name)
        (label, Django URL name, 'get' or 'post')
        (label, Django URL name, 'get' or 'post', color)
        (label, Django URL name, 'get' or 'post', color)
        (label, Django URL name, 'get' or 'post', color, pk_field_name)
        (label, Django URL name, 'get' or 'post', color, pk_field_name, javascript function name)

    Note:
        The magic is all done in :py:meth:`render_actions_column`, so if you want
        to see what's really going on, read that code.

    Examples:

        To make a button named "Edit" that goes to the django URL named
        ``core:model--edit``::

            ('Edit', 'core:model--edit')

        This renders a "button" something like this::

            <a href="/core/model/edit/?id=1" class="btn btn-secondary normal me-2">Edit</a>

        Make a button named "Delete" that goes to the django URL named
        ``core:model--delete`` as a ``POST``::

            ('Delete', 'core:model--delete', 'post')

        This renders a "button" something like this::

            <form class"form form-inline" action="/core/model/delete/" method="post">
                <input type="hidden" name="csrfmiddlewaretoken" value="__THE_TOKEN__">
                <input type="hidden" name="id" value="1">
                <input type="submit" value="Delete" class="btn btn-secondary normal me-2">
            </form>
    """

    #: Per row action buttons.  If not ``False``, this will simply add a
    #: rightmost column  named ``Actions`` with a button named
    #: :py:attr:`default_action_button_label` which when clicked will take the
    #: user to the
    actions: Any = False
    #: How big should each action button be? One of ``normal``, ``btn-lg``, or ``btn-sm``.
    action_button_size: str = 'normal'
    #: The label to use for the default action button
    default_action_button_label: str = 'View'
    #: The Bootstrap color class to use for the default action buttons
    default_action_button_color_class: str = 'secondary'

    def __init__(
        self,
        *args,
        actions: Any = None,
        action_button_size: str = None,
        default_action_button_label: str = None,
        default_action_button_color_class: str = None,
        **kwargs
    ):
        self.actions = actions if actions is not None else self.actions
        self.action_button_size = action_button_size if action_button_size else self.action_button_size
        self.default_action_button_label = (
            default_action_button_label
            if default_action_button_label else self.default_action_button_label
        )
        self.default_action_button_color_class = (
            default_action_button_color_class
            if default_action_button_color_class else self.default_action_button_color_class
        )
        if not self.action_button_size == 'normal':
            self.action_button_size_class = f"btn-{self.action_button_size}"
        else:
            self.action_button_size_class = ''
        super().__init__(*args, **kwargs)

    def get_template_context_data(self, **kwargs) -> Dict[str, Any]:
        if self.actions:
            self.add_column(field='actions', searchable=False, sortable=False)
            kwargs['has_actions'] = True
            kwargs['action_column'] = len(self.column_fields) - 1
        else:
            kwargs['has_actions'] = False
        return super().get_template_context_data(**kwargs)

    def get_content(self, **kwargs) -> str:
        if self.actions:
            self.add_column(field='actions', searchable=False, sortable=False)
        return super().get_content(**kwargs)

    def get_action_button(
        self,
        row: Any,
        label: str,
        url_name: str,
        method: str = 'get',
        color_class: str = 'secondary',
        attr: str = 'id',
        js_function_name: str = None
    ) -> str:
        if url_name:
            base = reverse(url_name)
            # FIXME: This assumes we're using QueryStringKwargsMixin, which people
            # outside our group don't use
            if method == 'get':
                url = f"{base}?{attr}={row.id}"
            else:
                url = base
        else:
            url = "javascript:void(0)"
        return self.get_action_button_with_url(row, label, url, method, color_class, attr, js_function_name)

    def get_action_button_url_extra_attributes(self, row: Any) -> str:
        return ""

    def get_action_button_with_url(
        self,
        row: Any,
        label: str,
        url: str,
        method: str = 'get',
        color_class: str = 'secondary',
        attr: str = 'id',
        js_function_name: str = None
    ) -> str:
        url_extra = self.get_action_button_url_extra_attributes(row)
        if url_extra:
            url = f"{url}&{url_extra}"
        if method == 'get':
            if js_function_name:
                link_extra = f'onclick="{js_function_name}({row.id});"'
            else:
                link_extra = ""
            return f'<a href="{url}" class="btn btn-{color_class} {self.action_button_size_class} me-2" {link_extra}>{label}</a>'
        token_input = f'<input type="hidden" name="csrfmiddlewaretoken" value="{self.csrf_token}">'
        id_input = f'<input type="hidden" name="{attr}" value="{row.id}">'
        button = f'<input type=submit value="{label}" class="btn btn-{color_class} {self.action_button_size_class} me-2">'
        form = f'<form class="form form-inline" action={url} method="post">{token_input}{id_input}{button}</form>'
        return form

    def get_conditional_action_buttons(self, row: Any) -> str:
        return ''

    def render_actions_column(self, row: Any, column: str) -> str:
        """
        Render the buttons in the "Actions" column.  This will only be called if
        :py:attr:`actions` is not falsy.  We rely on :py:attr:`actions` to be
        specified in a particular way in order for this to work; see
        :py:class:`ActionButtonsBySpecMixin` for information about how to
        specify button specs in :py:attr:`actions` is constructed.

        Args:
            row: the row data for which we are building action buttons
            column: unused

        Returns:
            The HTML to render into the "Actions" column for ``row``.
        """
        response = '<div class="d-flex flex-row justify-content-end">'
        if hasattr(row, 'get_absolute_url'):
            if callable(row.get_absolute_url):
                url = row.get_absolute_url()
            else:
                url = row.get_absolute_url
            view_button = self.get_action_button_with_url(
                row,
                self.default_action_button_label,
                url,
                color_class=self.default_action_button_color_class
            )
            response += view_button
        if not isinstance(self.actions, bool):
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


class DataTable(
    ActionsButtonsBySpecMixin,
    Widget,
    WidgetInitKwargsMixin,
    DatatableAJAXView
):
    """
    Extends :py:class:`DatatableAJAXView`.

    A widget that renders a `DataTables.js table <https://datatables.net/>`_.

    Keyword Args:
        width: The table width. Defaults to '100%'.
        height: The table height.
        title: The table title.
        searchable: Whether the table is searchable.
        paging: Whether the table is paged.
        page_length: The number of rows per page.
        small: Whether the row height is small.
        buttons: Whether the table has export buttons.
        striped: Whether the table is striped. Defaults to False.
        table_id: The table CSS id. Defaults to None.
        async: Whether the table is asynchronous. Defaults to True.
        data: The table data. Defaults to None.
        sort_ascending: Whether the table is sorted in ascending order. Defaults to True.
        action_button_size: The size of the action button. Defaults to 'normal'.
            Valid values are 'normal', 'sm', 'lg'.
    """

    template_file: str = 'wildewidgets/table.html'

    # dataTable specific configs

    #: How wide should we make the table?  Any CSS width string is valid.
    width: str = '100%'
    #: Use smaller font and row size?
    small: bool = False
    #: Stripe our rows so that different colors are used for even and odd
    #: rows?
    striped: bool = False
    #: How many rows should we show on each page
    page_length: int = 25
    #: If ``True``, sort rows ascending; otherwise descending.
    sort_ascending: bool = True
    #: Hide our paging, page length and search controls
    hide_controls: bool = False

    #: The CSS id to assign to the table.  The id will be ``datatable_table_{table_id}``
    table_id: Optional[str] = None

    #: Add the dataTable "Copy", "CSV", "Export" and "Print" buttons
    buttons: bool = False

    #: Whole table form actions.  If this is not ``None``, add a first column with
    #: checkboxes to each row, and a form that allows you to choose bulk actions
    #: to perform on all checked rows.
    form_actions = None
    #: THe URL to which to POST our form actions
    form_url: str = ''

    def __init__(
        self,
        *args,
        width: str = None,
        height: str = None,
        title: str = None,
        searchable: str = True,
        paging: str = True,
        page_length: int = None,
        small: bool = False,
        buttons: bool = False,
        striped: bool = False,
        table_id: str = None,
        sort_ascending: bool = None,
        data: List[Any] = None,
        **kwargs
    ):
        #: These are options for dataTable itself and get set in the JavaScript
        #: constructor for the table.
        self.options = {
            'width': width,
            'height': height,
            "title": title,
            "searchable": searchable,
            "paging": paging,
            "page_length": page_length,
            "small": small,
            "buttons": buttons,
            "striped": striped,
            "hide_controls": self.hide_controls
        }
        self.table_id = table_id if table_id else self.table_id
        # We have to do this this way instead of naming it above in the kwargs
        # because ``async`` is a reserved keyword
        self.async_if_empty: bool = kwargs.get('async', True)
        #: A mapping of field name to column definition
        self.column_fields: Dict[str, DataTableColumn] = {}
        #: A mapping of field name to column filter definition
        self.column_filters: Dict[str, DataTableFilter] = {}
        #: A list of column styles to apply
        self.column_styles: List[DataTableStyler] = []
        self.data = data if data else []
        self.sort_ascending = sort_ascending if sort_ascending is not None else self.sort_ascending

        self._form_actions = copy(self.form_actions)
        if self.has_form_actions():
            self.column_fields['checkbox'] = DataTableColumn(
                field='checkbox',
                verbose_name=' ',
                searchable=False,
                sortable=False
            )
        super().__init__(*args, **kwargs)

    def has_form_actions(self) -> bool:
        return self._form_actions is not None

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

    def add_column(
        self,
        field: str,
        verbose_name: str = None,
        searchable: bool = True,
        sortable: bool = True,
        align: str = 'left',
        head_align: str = 'left',
        visible: bool = True,
        wrap: bool = True
    ) -> None:
        """
        Add a column to our table.  This updates :py:attr:`column_fields`.

        Args:
            field: the name of the field that to render in this column

        Keyword Args:
            verbose_name: the label to use for the heading of this column
            searchable: if ``True``, include this column in global searches
            sortable: if ``True``, the table can be sorted by this column
            align: horizontal alignment for this column: ``left``, ``right``, ``center``
            visible: if ``False``, the column will be present in the table, but hidden
                from the user
            head_align: horizontal alignment for the header for this column: ``left``, ``right``, ``center`
            wrap: if ``True``, wrap contents in this column
        """
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

    def add_filter(self, field: str, dt_filter: DataTableFilter) -> None:
        """
        Add a column filter.  This updates :py:attr:`column_filters`.

        Args:
            field: the name of the field to filter
            dt_filter: a filter definition
        """
        self.column_filters[field] = dt_filter

    def remove_filter(self, field: str):
        """
        Remove a column filter.  This updates :py:attr:`column_filters`.

        Args:
            field: the name of the field for which to remove the filter
        """
        del self.column_filters[field]

    def add_styler(self, styler: DataTableStyler) -> None:
        styler.test_index = list(self.column_fields.keys()).index(styler.test_cell)
        if styler.target_cell:
            styler.target_index = list(self.column_fields.keys()).index(styler.target_cell)
        self.column_styles.append(styler)

    def build_context(self, **kwargs) -> Dict[str, Any]:
        kwargs['rows'] = self.data
        return kwargs

    def get_template_context_data(self, **kwargs) -> Dict[str, Any]:
        kwargs = super().get_template_context_data(**kwargs)
        has_filters = False
        filters = []
        for key, item in self.column_fields.items():
            if key in self.column_filters:
                filters.append((item, self.column_filters[key]))
                has_filters = True
            else:
                filters.append(None)
        if self.data or not self.async_if_empty:
            kwargs = self.build_context(**kwargs)
            kwargs['async'] = False
        else:
            kwargs['async'] = True
        kwargs['header'] = self.column_fields
        kwargs['has_form_actions'] = self.has_form_actions()
        kwargs['filters'] = filters
        kwargs['stylers'] = self.column_styles
        kwargs['has_filters'] = has_filters
        kwargs['options'] = self.options
        table_id = self.table_id if self.table_id else random.randrange(0, 1000)
        kwargs['name'] = f"datatable_table_{table_id}"
        kwargs['sort_ascending'] = self.sort_ascending
        kwargs["tableclass"] = self.__class__.__name__
        if not self.data:
            kwargs["extra_data"] = self.get_encoded_extra_data()
        kwargs["form"] = DataTableForm(self)
        if 'csrf_token' in kwargs:
            kwargs["csrf_token"] = kwargs['csrf_token']
        return kwargs

    def get_content(self, **kwargs) -> str:
        """
        Return the rendered dataTable HTML.

        Keyword Args:
            **kwargs: the template context

        Returns:
            The rendered datatable HTML
        """
        context = self.get_template_context_data(**kwargs)
        html_template = template.loader.get_template(self.template_file)
        return html_template.render(context)

    def __str__(self) -> str:
        return self.get_content()

    def add_row(self, **kwargs) -> None:
        row = []
        for field in self.column_fields:
            if field in kwargs:
                row.append(kwargs[field])
            else:
                row.append('')
        self.data.append(row)

    def render_checkbox_column(self, row: Any, column: str) -> str:
        return f'<input type="checkbox" name="checkbox" value="{row.id}">'


class ModelTableMixin:
    """
    This mixin is used to create a table from a :py:class:`Model`.  It provides methods
    to create and configure columns based on model fields and configuration.

    Example::

        from django.db import models
        from wildewidgets import DataTable, ModelTableMixin

        class Author(models.Model):

            full_name = models.CharField(...)

        class Book(models.Model):

            title = models.CharField(...)
            isbn = models.CharField(...)
            authors = models.ManyToManyField(Author)

        class BookModelTable(ModelTableMixin, DataTable):
            fields = ['title', 'authors__full_name', 'isbn']
            model = Book
            alignment = {'authors': 'left'}
            verbose_names = {'authors__full_name': 'Authors'}
            buttons = True
            striped = True

            def render_authors__full_name_column(self, row, column):
                authors = row.authors.all()
                if authors.count() > 1:
                    return f"{authors[0].full_name} ... "
                return authors[0].full_name
    """

    #: The Django model class for this table
    model: Optional[Type[models.Model]]

    #: This is either ``None``, the string ``__all__`` or a list of column names
    #: to use in our table.  For the list, entries can either be field names
    #: from our :py:attr:`model`, or names of computed fields that will be
    #: rendered with a ``render_FIELD_column`` method.  If ``None``, empty list
    #: or ``__all__``, display all fields on the :py:attr:`model`.
    fields: Optional[Union[str, List[str]]] = []
    #: The list of field names to hide by default
    hidden: List[str] = []
    #: A mapping of field name to table column heading
    verbose_names: Dict[str, str] = {}
    #: A list of field names that will not be sortable
    unsortable: List[str] = []
    #: A list of field names that will not be searched when doing a global table search
    unsearchable: List[str] = []
    #: A mapping of field name to data type.  This is used to do some automatic formatting
    #: of table values.
    field_types: Dict[str, str] = {}
    #: A mapping of field name to field alignment.  Valid values are ``left``, ``right``, and
    #: ``center``
    alignment: Dict[str, str] = {}
    bool_icons = {}

    def __init__(
        self,
        *args,
        fields: Optional[Union[str, List[str]]] = None,
        hidden: List[str] = None,
        verbose_names: List[str] = None,
        unsortable: List[str] = None,
        unsearchable: List[str] = None,
        field_types: Dict[str, str] = None,
        alignment: Dict[str, str] = None,
        bool_icons: Dict[str, str] = None,
        **kwargs
    ):
        self.fields = fields if fields else deepcopy(self.fields)
        self.hidden = hidden if hidden else deepcopy(self.hidden)
        self.verbose_names = verbose_names if verbose_names else deepcopy(self.verbose_names)
        self.unsortable = unsortable if unsortable else deepcopy(self.unsortable)
        self.unsearchable = unsearchable if unsearchable else deepcopy(self.unsearchable)
        self.field_types = field_types if field_types else deepcopy(self.field_types)
        self.alignment = alignment if alignment else deepcopy(self.alignment)
        self.bool_icons = bool_icons if bool_icons else deepcopy(self.bool_icons)
        super().__init__(*args, **kwargs)

        #: A mapping of field name to Django field class
        self.model_fields: Dict[str, models.Field] = {}
        #: A mapping of field name to Django related field class
        self.related_fields: Dict[str, models.Field] = {}
        #: A list of names of our model fields
        self.field_names: List[str] = []

        # Build our mapping of all known fields on :py:attr:`model`
        for field in self.model._meta.get_fields():
            if field.name == 'id':
                continue
            self.model_fields[field.name] = field
            self.field_names.append(field.name)

        # Find our related fields -- these are in Django QuerySet format, e.g.
        # parent__child or parent__child__grandchild
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

    def get_related_model(
        self,
        current_model: Type[models.Model],
        field_name: str
    ) -> models.Model:
        return current_model._meta.get_field(field_name).related_model

    def get_related_field(
        self,
        current_model: models.Model,
        name: str
    ) -> Optional[models.Field]:
        """
        Given ``name``, a field specifier in Django QuerySet format, e.g.
        ``parent__child`` or ``parent__child__grandchild``, return the field
        instance that represents that field on the appropriate related model.

        Args:
            current_model:  the model for the leftmost field in ``name``
            name: the field specfier

        Returns:
            the :py:class:`Field` instance, or ``None`` if we couldn't find one.
        """
        name_fields: List[str] = name.split('__')
        if len(name_fields) == 1:
            # This is not a related field specifier
            return None
        # Walk through the fields and find the Django model for the last
        # field in the spec
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

    def get_field(self, field_name: str) -> Optional[models.Field]:
        if field_name in self.model_fields:
            field = self.model_fields[field_name]
        elif field_name in self.related_fields:
            field = self.related_fields[field_name]
        else:
            field = None
        return field

    def set_standard_column_attributes(self, field_name: str, kwargs: Dict[str, Any]) -> None:
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

    def load_field(self, field_name: str) -> None:
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

    def load_all_fields(self) -> None:
        for field_name in self.field_names:
            self.load_field(field_name)

    def render_currency_type_column(self, value: Any) -> str:
        return f"${value}"

    def render_bool_type_column(self, value: Any) -> str:
        if value == "True":
            return '<i class="bi-check-lg text-success"><span style="display:none">True</span></i>'
        return ""

    def render_bool_icon_column(self, value: Any, icon_data: Tuple[str, str]) -> str:
        if len(icon_data) == 0:
            return value
        if value == "True":
            return f"<i class='bi-{icon_data[0][0]} {icon_data[0][1]}'><span style='display:none'>True</span></i>"
        if len(icon_data) > 1:
            return f"<i class='bi-{icon_data[1][0]} {icon_data[1][1]}'><span style='display:none'>False</span></i>"
        return ""

    def render_datetime_type_column(self, value: datetime.datetime) -> str:
        datetime_format = "%m/%d/%Y %H:%M"
        if hasattr(settings, 'WILDEWIDGETS_DATETIME_FORMAT'):
            datetime_format = settings.WILDEWIDGETS_DATETIME_FORMAT
        if value:
            return value.strftime(datetime_format)
        return ""

    def render_date_type_column(self, value: datetime.date) -> str:
        date_format = "%m/%d/%Y"
        if hasattr(settings, 'WILDEWIDGETS_DATE_FORMAT'):
            date_format = settings.WILDEWIDGETS_DATE_FORMAT
        if value:
            return value.strftime(date_format)
        return ""

    def render_column(self, row: Any, column: str) -> str:
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


class BasicModelTable(ModelTableMixin, DataTable):
    """
    This class is used to create a table from a :py:class:`Model`.  It provides a full
    featured table with a minimum of code. Many derived classes will only need
    to define class variables.

    Example::

        class BookModelTable(BasicModelTable):
            fields = ['title', 'authors__full_name', 'isbn']
            model = Book
            alignment = {'authors': 'left'}
            verbose_names = {'authors__full_name': 'Authors'}
            buttons = True
            striped = True

            def render_authors__full_name_column(self, row, column):
                authors = row.authors.all()
                if authors.count() > 1:
                    return f"{authors[0].full_name} ... "
                return authors[0].full_name
    """
    pass
