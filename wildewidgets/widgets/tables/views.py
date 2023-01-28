from functools import lru_cache
import logging
import re

from typing import Any, Dict, List, Optional, Tuple, Type, Union

from django.db import models
from django.db.models import Q
from django.utils.html import escape

from wildewidgets.views import JSONResponseView

logger = logging.getLogger(__name__)


class DatatableMixin:

    #: Use this
    model: Optional[Type[models.Model]] = None

    #: The names of the columns to display in our table
    columns: List[str] = []
    #: internal cache for columns definition
    _columns = []
    #: The list of column names by which the table will be ordered.
    order_columns: List[str] = []

    #: The max number of of records that will be returned, so that we can protect our
    #: our server from rendering huge amounts of data
    max_display_length: int = 100
    #: Set to ``True`` if you are using datatables < 1.10
    pre_camel_case_notation: bool = False
    #: Replace any column value that is ``None`` with this string
    none_string: str = ''
    # If set to ``True`` then values returned by :py:meth:`render_column`` will be escaped
    escape_values: bool = True
    #: This gets set by the dataTables Javascript when it does the AJAX call
    columns_data: List[Dict[str, Any]] = []
    #: This determines the type of results. If the AJAX call passes us a data attribute
    #: that is not an integer, it expects a dictionary with specific fields in
    #: the response, see: `dataTables columns.data
    #: <https://datatables.net/reference/option/columns.data>`_
    is_data_list: bool = True

    FILTER_ISTARTSWITH: str = 'istartswith'
    FILTER_ICONTAINS: str = 'icontains'

    def __init__(
        self,
        model: Type[models.Model] = None,
        order_columns: List[str] = None,
        max_display_length: int = None,
        none_string: str = None,
        is_data_list: bool = None,
        escape_values: bool = None,
        **kwargs
    ):
        self.model = model if model else self.model
        self.order_columns = order_columns if order_columns else self.order_columns
        self.max_display_length = max_display_length if max_display_length else self.max_display_length
        self.none_string = none_string if none_string else self.none_string
        self.is_data_list = is_data_list if is_data_list else self.is_data_list
        self.escape_values = escape_values if escape_values else self.escape_values
        super().__init__(**kwargs)

    @property
    def _querydict(self):
        if self.request.method == 'POST':
            return self.request.POST
        return self.request.GET

    def get_initial_queryset(self) -> models.QuerySet:
        if not self.model:
            raise NotImplementedError(
                "Need to provide a model or implement get_initial_queryset!"
            )
        return self.model.objects.all()

    def get_filter_method(self) -> str:
        """
        Returns preferred Django queryset filter method, e.g. ``istartswith``,
        ``icontains``.

        This will be used to filter querysets doing global searches and single
        column filtering.

        Returns:
            The filter method string.
        """
        return self.FILTER_ISTARTSWITH

    def initialize(self, *args, **kwargs):
        """
        Determine which version of DataTables is being used - there are
        differences in parameters sent by DataTables < 1.10.x
        """
        if 'iSortingCols' in self._querydict:
            self.pre_camel_case_notation = True

    def get_order_columns(self) -> List[str]:
        """
        Return list of columns used for ordering.

        By default returns :py:attr`order_columns` but if these are not defined
        it tries to get columns from the request using the ``columns[i][name]``
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
                # if self.is_data_list is False then we have a column name in
                # the 'data' attribute, otherwise 'data' attribute is an integer
                # with column index
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

    def get_columns(self) -> List[str]:
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
    def _column_value(obj: Any, key: str) -> Any:
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
        if hasattr(obj, f'get_{parts[-1]}_display'):
            value = getattr(obj, f'get_{parts[-1]}_display')()
        else:
            value = self._column_value(obj, parts[-1])

        if value is None:
            value = self.none_string if value is None else value
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

    def ordering(self, qs: models.QuerySet) -> models.QuerySet:
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
            sort_key = f'order[{sorting_cols}][column]'
            while sort_key in self._querydict:
                sorting_cols += 1
                sort_key = f'order[{sorting_cols}][column]'

        order = []
        order_columns = self.get_order_columns()

        for i in range(sorting_cols):
            # sorting column
            sort_dir = 'asc'
            try:
                if self.pre_camel_case_notation:
                    sort_col = int(self._querydict.get(f'iSortCol_{i}'))
                    # sorting order
                    sort_dir = self._querydict.get(f'sSortDir_{i}')
                else:
                    sort_col = int(self._querydict.get(f'order[{i}][column]'))
                    # sorting order
                    sort_dir = self._querydict.get(f'order[{i}][dir]')
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

    def paging(self, qs: models.QuerySet) -> models.QuerySet:
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

    def extract_datatables_column_data(self) -> List[Dict[str, str]]:
        """
        Helper method to extract columns data from request as passed by Datatables 1.10+.
        """
        request_dict = self._querydict
        col_data = []
        if not self.pre_camel_case_notation:
            counter = 0
            data_name_key = f'columns[{counter}][name]'
            while data_name_key in request_dict:
                searchable = request_dict.get(f'columns[{counter}][searchable]') == 'true'
                orderable = request_dict.get(f'columns[{counter}][orderable]') == 'true'
                col_data.append(
                    {
                        'name': request_dict.get(data_name_key),
                        'data': request_dict.get(f'columns[{counter}][data]'),
                        'searchable': searchable,
                        'orderable': orderable,
                        'search.value': request_dict.get(f'columns[{counter}][search][value]'),
                        'search.regex': request_dict.get(f'columns[{counter}][search][regex]')
                    }
                )
                counter += 1
                data_name_key = f'columns[{counter}][name]'
        return col_data

    def prepare_results(
        self,
        qs: models.QuerySet
    ) -> Union[List[List[str]], List[Dict[str, Any]]]:
        data = []
        for item in qs:
            if self.is_data_list:
                data.append([self.render_column(item, column) for column in self._columns])
            else:
                data.append({
                    col_data['data']: self.render_column(item, col_data['data'])
                    for col_data in self.columns_data
                })

        return data

    def handle_exception(self, e):
        logger.exception(str(e))
        raise e

    def get_context_data(self, *args, **kwargs):
        try:
            self.initialize(*args, **kwargs)

            # prepare columns data (for DataTables 1.10+)
            self.columns_data = self.extract_datatables_column_data()

            # determine the response type based on the 'data' field passed from
            # JavaScript https://datatables.net/reference/option/columns.data
            # col['data'] can be an integer (return list) or string (return
            # dictionary) we only check for the first column definition here as
            # there is no way to return list and dictionary at once
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

            qs = self.get_initial_queryset()
            total_records = qs.count()
            qs = self.filter_queryset(qs)
            total_display_records = qs.count()
            qs = self.ordering(qs)
            qs = self.paging(qs)

            # prepare output data
            if self.pre_camel_case_notation:
                ret = {
                    'sEcho': int(self._querydict.get('sEcho', 0)),
                    'iTotalRecords': total_records,
                    'iTotalDisplayRecords': total_display_records,
                    'aaData': self.prepare_results(qs)
                }
            else:
                ret = {
                    'draw': int(self._querydict.get('draw', 0)),
                    'recordsTotal': total_records,
                    'recordsFiltered': total_display_records,
                    'data': self.prepare_results(qs)
                }
            return ret
        except Exception as e:  # pylint: disable=broad-except
            return self.handle_exception(e)


class BaseDatatableView(DatatableMixin, JSONResponseView):
    pass


class DatatableAJAXView(BaseDatatableView):
    """
    This is a JSON view that a DataTables.js table can hit for its AJAX queries.
    """

    def columns(self, querydict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse the request we got from the DataTables AJAX request
        (``querydict``) from a list of strings to a more useful nested dict.
        We'll use this to more readily figure out what we need to be doing.

        A single column's data in the querystring we got from datatables looks
        like::

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

        Args:
            querydict: dict of all key, value pairs from the AJAX request.

        Returns:
            The dictionary of column definitions keyed by column name
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
    def searchable_columns(self) -> List[str]:
        """
        Return the list of all column names from our DataTable that are marked
        as "searchable".

        Returns:
            List of searchable columns.
        """
        return [
            key for key, value in self.columns(self._querydict).items()
            if value['searchable']
        ]

    def column_specific_searches(self) -> List[Tuple[str, str]]:
        """
        Look through the request data we got from the DataTable AJAX request for
        any single-column searches.  These will look like
        ``column[$number][search][value]`` in the request.

        Returns:
            A list of 2-tuples that look like ``(column name, search string)``
        """
        return [
            (key, value['search']['value'])
            for key, value in self.columns(self._querydict).items()
            if value['search']['value']
        ]

    def single_column_filter(
        self,
        qs: models.QuerySet,
        column: str,
        value: str
    ) -> models.QuerySet:
        """
        Filter our queryset by a single column.  Columns will be searched by
        ``__icontains``.

        This gets executed when someone runs a search on a single DataTables.js
        column::

            data_table.column($number).search($search_string);

        If you want to implement a different search filter for a particular
        column, add a ``search_COLUMN_column(self, qs, column, value)`` method
        that returns a QuerySet to your subclass and that will be called
        instead.

        Example::

            def search_foobar_column(self, qs, column, value):
                if value == 'something':
                    qs = qs.filter(foobar__attribute=True)
                elif value == 'other_thing':
                    qs = qs.filter(foobar__other_attribute=False)
                return qs

        Args:
            qs: the Django QuerySet
            column: the dataTables data attribute for the column we're interested in
            value: the search string

        Returns:
            An appropriately filtered :py:class:`QuerySet`
        """
        attr_name = f'filter_{column}_column'
        if hasattr(self, attr_name):
            qs = getattr(self, attr_name)(qs, column, value)
        elif column in self.searchable_columns():
            kwarg_name = f'{column}__icontains'
            qs = qs.filter(**{kwarg_name: value})
        return qs

    def search_query(self, qs: models.QuerySet, value: str) -> models.Q:
        """
        Return an ORed Q() object that will search the searchable fields for ``value``

        Args:
            qs: the Django QuerySet
            value: the search string

        Returns:
            A properly formatted :py:class:`Q` object
        """
        # FIXME: we doesn't use qs, so why are we accepting it as a parameter
        query = None
        for column in self.searchable_columns():
            attr_name = f'search_{column}_column'
            if hasattr(self, attr_name):
                q = getattr(self, attr_name)(column, value)
            else:
                kwarg_name = f'{column}__icontains'
                q = Q(**{kwarg_name: value})
            query = query | q if query else q
        return query

    def search(self, qs: models.QuerySet, value: str) -> models.QuerySet:
        """
        Filter our queryset across all of our searchable columns for ``value``.

        This gets executed when someone runs a search over the whole
        DataTables.js table::

            data_table.search($search_string);

        This is what happens when the user uses the "Search" input on the
        DataTable.

        Args:
            qs: the Django QuerySet
            value: the search string

        Returns:
            Our ``qs`` filtered by our searchable columns.
        """
        query = self.search_query(qs, value)
        qs = qs.filter(query).distinct()
        return qs

    def filter_queryset(self, qs: models.QuerySet) -> models.QuerySet:
        """
        We're overriding the default filter_queryset(method) here so we can
        implement proper searches on our pseudo-columns "responded" and
        "disabled", and do column specific searches, as well as doing general
        searches across our regular CharField columns.
        """
        column_searches = self.column_specific_searches()
        if column_searches:
            for column, value in column_searches:
                qs = self.single_column_filter(qs, column, value)
        value = self.request.GET.get('search[value]', None)
        if value:
            qs = self.search(qs, value)
        return qs

    def _render_column(self, row: Any, column: str) -> str:
        """
        When defining our DataTable config, we declare DataTable columns that
        access columns of models of foreign keys on our model with ``__``
        notation.  Convert the ``__`` to ``.`` before trying to render the data
        so that things will work correctly.

        Args:
            row: A Django model instance
            column: the name of the column to render

        Return:
            The rendered column as valid HTML.
        """
        column = re.sub('__', '.', column)
        return super()._render_column(row, column)

    def render_column(self, row: Any, column: str) -> str:
        """
        Return the data to add to the DataTable for column ``column`` of the
        table row corresponding to the model object ``row``.

        If you want to implement special rendering a particular column (for
        instance to display something about an object that doesn't map directly
        to a model column), add a ``render_COLUMN_column(self, row, column)``
        method that returns a string to your subclass and that will be called
        instead.

        Example::

            def render_foobar_column(self, row: Any, column: str) -> str:
                return 'some data'

        Args:
            row: A Django model instance
            column: the name of the column to render

        Return:
            The rendered column as valid HTML.
        """
        attr_name = f'render_{column}_column'
        if hasattr(self, attr_name):
            return getattr(self, attr_name)(row, column)
        return super().render_column(row, column)
