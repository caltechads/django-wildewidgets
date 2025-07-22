from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Final, NoReturn

from django.db.models import Model, Q
from django.utils.html import escape

from wildewidgets.views import JSONResponseView

if TYPE_CHECKING:
    from django.db import models

logger = logging.getLogger(__name__)


class DatatableMixin:
    """
    A mixin that provides server-side processing for jQuery DataTables.

    This mixin handles all the server-side processing required by jQuery DataTables,
    including sorting, filtering, searching, and pagination. It can work with Django
    QuerySets and provides a customizable framework for rendering data.

    The mixin works with both older (<1.10) and newer versions of DataTables,
    automatically adapting to the format of parameters sent by the client.

    Example:
        .. code-block:: python

            class MyDatatableView(DatatableMixin, JSONResponseView):
                model = MyModel
                columns = ['id', 'name', 'description']
                order_columns = ['id', 'name', 'description']

                def render_description_column(self, row, column):
                    return f"{row.description[:50]}..."

    """

    #: The Django model that this datatable will be based on.
    #: If not provided, you must implement the :py:meth:`get_initial_queryset`
    #: method to return a queryset.
    model: type[models.Model] | None = None

    #: The names of the columns to display in our table
    columns: list[str] = []  # noqa: RUF012
    #: internal cache for columns definition
    _columns: list[Any] = []  # noqa: RUF012
    #: The list of column names by which the table will be ordered.
    order_columns: list[str] = []  # noqa: RUF012

    #: The max number of of records that will be returned, so that we can protect our
    #: our server from rendering huge amounts of data
    max_display_length: int = 100
    #: Set to ``True`` if you are using datatables < 1.10
    pre_camel_case_notation: bool = False
    #: Replace any column value that is ``None`` with this string
    none_string: str = ""
    #: If set to ``True`` then values returned by :py:meth:`render_column`` will
    #: be escaped
    escape_values: bool = True
    #: This gets set by the dataTables Javascript when it does the AJAX call
    columns_data: list[dict[str, Any]] = []  # noqa: RUF012
    #: This determines the type of results. If the AJAX call passes us a data attribute
    #: that is not an integer, it expects a dictionary with specific fields in
    #: the response, see: `dataTables columns.data
    #: <https://datatables.net/reference/option/columns.data>`_
    is_data_list: bool = True

    #: The filter method to use for global searches and single column filtering
    #: for case-insensitive "startswith" searches
    FILTER_ISTARTSWITH: Final[str] = "istartswith"
    #: The filter method to use for global searches and single column filtering
    #: for case-insensitive "contins" searches
    FILTER_ICONTAINS: Final[str] = "icontains"

    def __init__(
        self,
        model: type[models.Model] | None = None,
        order_columns: list[str] | None = None,
        max_display_length: int | None = None,
        none_string: str | None = None,
        is_data_list: bool | None = None,
        escape_values: bool | None = None,
        **kwargs,
    ):
        self.model = model if model else self.model
        self.order_columns = order_columns if order_columns else self.order_columns
        self.max_display_length = (
            max_display_length if max_display_length else self.max_display_length
        )
        self.none_string = none_string if none_string else self.none_string
        self.is_data_list = is_data_list if is_data_list else self.is_data_list
        self.escape_values = escape_values if escape_values else self.escape_values
        super().__init__(**kwargs)

    @property
    def _querydict(self):
        if self.request.method == "POST":  # type: ignore[attr-defined]
            return self.request.POST  # type: ignore[attr-defined]
        return self.request.GET  # type: ignore[attr-defined]

    def get_initial_queryset(self) -> models.QuerySet:
        """
        Get the initial queryset for the datatable.

        By default, returns all objects from the model specified in the `model`
        attribute.  Override this method to provide custom querysets, filtering
        by user permissions, or any other logic needed to determine the base
        dataset.

        Returns:
            QuerySet: The initial queryset for the datatable

        Raises:
            NotImplementedError: If no model is specified and this method is not
                overridden

        """
        if not self.model:
            msg = "You need to provide a model or implement get_initial_queryset"
            raise NotImplementedError(msg)
        return self.model.objects.all()

    def get_filter_method(self) -> str:
        """
        Get the preferred Django queryset filter method for searches.

        This determines how text searching is performed on columns. By default, uses
        "istartswith" for case-insensitive prefix matching, but can be overridden to
        use other methods like "icontains" for substring matching.

        Returns:
            str: The filter method string (e.g., "istartswith", "icontains")

        """
        return self.FILTER_ISTARTSWITH

    def initialize(self, *args, **kwargs):  # noqa: ARG002
        """
        Initialize the datatable by determining the DataTables version in use.

        This method checks request parameters to detect whether the client is using
        DataTables <1.10 (which uses different parameter naming conventions), and
        configures the mixin accordingly.

        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments

        """
        if "iSortingCols" in self._querydict:
            self.pre_camel_case_notation = True

    def get_order_columns(self) -> list[str]:
        """
        Get the list of columns that can be used for ordering/sorting.

        This method returns the columns that can be sorted in the datatable. It first
        checks the :py:attr:`order_columns` attribute, then falls back to
        extracting column information from the dataTables.js request parameters if
        using newer versions.

        Returns:
            list[str]: List of column names that can be sorted

        """
        if self.order_columns or self.pre_camel_case_notation:
            return self.order_columns

        # try to build list of order_columns using request data
        order_columns = []
        for column_def in self.columns_data:
            if column_def["name"] or not self.is_data_list:
                # if self.is_data_list is False then we have a column name in
                # the 'data' attribute, otherwise 'data' attribute is an integer
                # with column index
                if column_def["orderable"]:
                    if self.is_data_list:
                        order_columns.append(column_def["name"])
                    else:
                        order_columns.append(column_def.get("data"))
                else:
                    order_columns.append("")
            else:
                # fallback to columns
                order_columns = self._columns
                break

        self.order_columns = order_columns
        return order_columns

    def get_columns(self) -> list[str]:
        """
        Get the list of columns to display in the datatable.

        This method determines which columns will be included in the response.
        It first checks the :py:class:`columns` attribute, then falls back to
        extracting column information from the dataTables.js request parameters
        if using newer versions.

        Returns:
            list[str]: List of column names to display

        """
        if self.columns or self.pre_camel_case_notation:
            return self.columns

        columns = []
        for column_def in self.columns_data:
            # if self.is_data_list is True then 'data' atribute is an integer -
            # column index, so we cannot use it as a column name, let's try
            # 'name' attribute instead
            col_name = column_def["name"] if self.is_data_list else column_def["data"]
            if col_name:
                columns.append(col_name)
            else:
                return self.columns

        return columns

    @staticmethod
    def _column_value(obj: Any, key: str) -> Any:
        """
        Extract a value from a model instance or dictionary.

        This helper method retrieves attribute or dictionary values safely, handling
        nested attribute access with dot notation.

        Args:
            obj: :py:class:`~django.db.models.Model` instance or dictionary for
                the current row
            key: Attribute or key name to retrieve

        Returns:
            Any: The value from the object, or None if not found

        """
        if isinstance(obj, dict):
            return obj.get(key, None)

        return getattr(obj, key, None)

    def _render_column(self, row: Any, column: str) -> str:
        """
        Render a column value from a model instance or dictionary.

        This internal method handles the actual value extraction and formatting,
        including support for Django's choice fields via ``get_FIELDNAME_display``
        methods, nested attribute access with dot notation, and HTML escaping.

        Args:
            row: :py:class:`~django.db.models.Model` instance or dictionary for
                the current row
            column: Column name or path (can use dot notation for nested access)

        Returns:
            str: The rendered value as a string

        """
        # try to find rightmost object
        obj = row
        parts = column.split(".")
        for part in parts[:-1]:
            if obj is None:
                break
            obj = getattr(obj, part)

        # try using get_OBJECT_display for choice fields
        if hasattr(obj, f"get_{parts[-1]}_display"):
            value = getattr(obj, f"get_{parts[-1]}_display")()
        else:
            value = self._column_value(obj, parts[-1])

        if value is None:
            value = self.none_string if value is None else value
        if self.escape_values:
            value = escape(value)

        return value

    def render_column(self, row: Any, column: str) -> str:
        """
        Render a column value for display in the datatable.

        This is the main method for formatting column values. Override this or create
        methods named ``get_FIELDNAME_display`` on your Django model to
        customize how specific columns are displayed.  See
        :py:meth:`_render_column` for details on how to implement custom
        rendering logic.

        Args:
            row: :py:class:`~django.db.models.Model` instance or dictionary for
                the current row
            column: Column name

        Returns:
            str: The rendered value as a string, ready for display

        """
        return self._render_column(row, column)

    def ordering(self, qs: models.QuerySet) -> models.QuerySet[Model]:  # noqa: PLR0912
        """
        Apply ordering to the queryset based on dataTables.js parameters.

        This method parses sorting parameters from the dataTables.js request
        and applies them to the queryset. It supports multi-column sorting and
        handles both older and newer dataTables.js parameter formats.

        Args:
            qs: The queryset to order

        Returns:
            models.QuerySet: The ordered queryset

        """
        # Number of columns that are used in sorting
        sorting_cols = 0
        if self.pre_camel_case_notation:
            try:
                sorting_cols = int(self._querydict.get("iSortingCols", 0))
            except ValueError:
                sorting_cols = 0
        else:
            sort_key = f"order[{sorting_cols}][column]"
            while sort_key in self._querydict:
                sorting_cols += 1
                sort_key = f"order[{sorting_cols}][column]"

        order = []
        order_columns = self.get_order_columns()

        for i in range(sorting_cols):
            # sorting column
            sort_dir = "asc"
            try:
                if self.pre_camel_case_notation:
                    sort_col = int(self._querydict.get(f"iSortCol_{i}"))
                    # sorting order
                    sort_dir = self._querydict.get(f"sSortDir_{i}")
                else:
                    sort_col = int(self._querydict.get(f"order[{i}][column]"))
                    # sorting order
                    sort_dir = self._querydict.get(f"order[{i}][dir]")
            except ValueError:
                sort_col = 0

            sdir = "-" if sort_dir == "desc" else ""
            sortcol = order_columns[sort_col]
            if not sortcol:
                continue

            # pylint: disable=consider-using-f-string
            if isinstance(sortcol, list):
                for sc in sortcol:
                    order.append("{}{}".format(sdir, sc.replace(".", "__")))  # noqa: PERF401
            else:
                order.append("{}{}".format(sdir, sortcol.replace(".", "__")))

        if order:
            return qs.order_by(*order)
        return qs

    def paging(self, qs: models.QuerySet) -> models.QuerySet:
        """
        Apply pagination to the queryset based on dataTables.js parameters.

        This method extracts pagination parameters (start position and length)
        from the dataTables.js request and slices the queryset accordingly.

        Args:
            qs: The queryset to paginate

        Returns:
            models.QuerySet: The paginated queryset

        """
        if self.pre_camel_case_notation:
            limit = min(
                int(self._querydict.get("iDisplayLength", 10)), self.max_display_length
            )
            start = int(self._querydict.get("iDisplayStart", 0))
        else:
            limit = min(int(self._querydict.get("length", 10)), self.max_display_length)
            start = int(self._querydict.get("start", 0))
        # if pagination is disabled ("paging": false)
        if limit == -1:
            return qs
        offset = start + limit
        return qs[start:offset]

    def extract_datatables_column_data(self) -> list[dict[str, str]]:
        """
        Extract column configuration data from the dataTables.js request.

        This method parses the complex column configuration parameters sent by
        dataTables.js 1.10+ into a more manageable structure for internal use.

        Returns:
            list[dict[str, str]]: List of column configuration dictionaries

        """
        request_dict = self._querydict
        col_data = []
        if not self.pre_camel_case_notation:
            counter = 0
            data_name_key = f"columns[{counter}][name]"
            while data_name_key in request_dict:
                searchable = (
                    request_dict.get(f"columns[{counter}][searchable]") == "true"
                )
                orderable = request_dict.get(f"columns[{counter}][orderable]") == "true"
                col_data.append(
                    {
                        "name": request_dict.get(data_name_key),
                        "data": request_dict.get(f"columns[{counter}][data]"),
                        "searchable": searchable,
                        "orderable": orderable,
                        "search.value": request_dict.get(
                            f"columns[{counter}][search][value]"
                        ),
                        "search.regex": request_dict.get(
                            f"columns[{counter}][search][regex]"
                        ),
                    }
                )
                counter += 1
                data_name_key = f"columns[{counter}][name]"
        return col_data

    def prepare_results(
        self, qs: models.QuerySet
    ) -> list[list[str]] | list[dict[str, Any]]:
        """
        Transform queryset results into the format expected by dataTables.js.

        This method converts Django model instances into either:

        - Lists of values (when :py:attr:`is_data_list` is True)
        - Dictionaries mapping column names to values (when
          :py:attr:`is_data_list` is False)

        It calls :py:meth:`render_column` for each value to allow custom formatting.

        Args:
            qs: The queryset containing the results to display

        Returns:
            Either a list of lists (row-based format) or a list of dictionaries
            (column-based format) depending on the DataTables configuration

        """
        if self.is_data_list:
            return [
                [self.render_column(item, column) for column in self._columns]
                for item in qs
            ]
        _dict_data: list[dict[str, Any]] = []
        for item in qs:
            _dict_data.append(  # noqa: PERF401
                {
                    col_data["data"]: self.render_column(item, col_data["data"])
                    for col_data in self.columns_data
                }
            )
        return _dict_data

    def handle_exception(self, e: Exception) -> NoReturn:
        """
        Handle exceptions that occur during processing.

        This method logs the exception and re-raises it by default. Override
        this method to implement custom exception handling.

        Args:
            e: The exception that was raised

        Raises:
            Exception: Re-raises the original exception

        """
        logger.exception(str(e))
        raise e

    def get_context_data(self, *args, **kwargs):
        """
        Process the DataTables request and prepare the response data.

        This is the main entry point that:

        1. Initializes the configuration based on the request
        2. Gets the initial queryset
        3. Applies filtering, sorting, and pagination
        4. Formats the results as expected by DataTables

        Args:
            *args: Variable length argument list

        Keyword Args:
            **kwargs: Arbitrary keyword arguments

        Returns:
            dict: Response data in the format expected by DataTables

        Note:
            The returned dictionary contains different keys depending on the
            dataTables.js version in use.

        """
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
                    int(self.columns_data[0]["data"])
                    self.is_data_list = True
                except ValueError:
                    pass

            # prepare list of columns to be returned
            self._columns = self.get_columns()

            qs = self.get_initial_queryset()
            total_records = qs.count()
            qs = self.filter_queryset(qs)  # type: ignore[attr-defined]
            total_display_records = qs.count()
            qs = self.ordering(qs)
            qs = self.paging(qs)

            # prepare output data
            if self.pre_camel_case_notation:
                ret = {
                    "sEcho": int(self._querydict.get("sEcho", 0)),
                    "iTotalRecords": total_records,
                    "iTotalDisplayRecords": total_display_records,
                    "aaData": self.prepare_results(qs),
                }
            else:
                ret = {
                    "draw": int(self._querydict.get("draw", 0)),
                    "recordsTotal": total_records,
                    "recordsFiltered": total_display_records,
                    "data": self.prepare_results(qs),
                }
        except Exception as e:  # noqa: BLE001
            return self.handle_exception(e)
        else:
            return ret


class BaseDatatableView(DatatableMixin, JSONResponseView):  # type: ignore[misc]
    """
    Base view for handling dataTables.js server-side processing.

    This class combines the dataTables.js processing functionality from
    :py:class:`DatatableMixin` with the JSON response handling from
    :py:class:`wildewidgets.JSONResponseView` to create a complete server-side
    processing view for dataTables.js.

    Extend this class and override the necessary methods to create a custom
    dataTables.js server-side processing view.
    """


class DatatableAJAXView(BaseDatatableView):
    """
    Enhanced view for handling dataTables.js AJAX requests with advanced features.

    This class extends :py:class:`BaseDatatableView` with additional functionality for:

    - Advanced column configuration parsing
    - Per-column filtering and searching
    - Support for dotted attribute notation and relationship traversal
    - Custom column rendering based on method naming conventions

    It's designed to be extended for specific datatables, with custom filtering
    and rendering logic implemented through method overrides.

    Example:
        .. code-block:: python

            class UserTableView(DatatableAJAXView):
                model = User
                columns = ['id', 'username', 'email', 'is_staff', 'date_joined']

                def render_is_staff_column(self, row, column):
                    return '✓' if row.is_staff else '✗'

                def render_date_joined_column(self, row, column):
                    return row.date_joined.strftime('%Y-%m-%d')

    """

    def columns(self, querydict: dict[str, Any]) -> dict[str, Any]:  # type: ignore[override]
        """
        Parse dataTables.js column configuration into a more usable format.

        This method converts the flattened column configuration from dataTables.js
        into a nested dictionary structure that's easier to work with. It maps
        column data by column name rather than index for more intuitive access.

        Note:
            This overrides the :py:attr:`columns` attribute from
            :py:class:`DatatableMixin` to provide a more advanced parsing
            mechanism.

        Args:
            querydict: The query parameters from the dataTables.js request

        Returns:
            dict[str, Any]: Dictionary mapping column names to their configuration

        """
        # First organize by column index, then transform to column name indexing
        by_number = self._parse_columns_by_index(querydict)
        return self._convert_to_name_indexed(by_number)

    def _parse_value(self, value: str) -> bool | str:
        """
        Convert string boolean values to Python booleans.

        Args:
            value: The string value to parse

        Returns:
            bool | str: Returns True or False for "true" or "false", otherwise
            returns the original value

        """
        if value == "true":
            return True
        if value == "false":
            return False
        return value

    def _parse_columns_by_index(
        self, querydict: dict[str, Any]
    ) -> dict[str, dict[str, Any]]:
        """
        Parse column parameters and organize by column index.

        Handles both direct attributes ``(columns[n][attr])`` and
        nested attributes ``(columns[n][attr][subattr])``.

        Args:
            querydict: The query parameters from the DataTables request

        Returns:
            dict[str, dict[str, Any]]: Dictionary mapping column index to its attributes
            and values, structured for easy access by column number.

        """
        by_number: dict[str, dict[str, Any]] = {}

        for key, value in querydict.items():
            if not key.startswith("columns"):
                continue

            parts = key.split("[")
            if len(parts) < 3:  # noqa: PLR2004
                continue

            # Extract key components
            column_number = parts[1][:-1]  # "n" from columns[n]
            column_attribute = parts[2][:-1]  # "attr" from [attr]

            # Initialize dict for this column if needed
            if column_number not in by_number:
                by_number[column_number] = {"column_number": int(column_number)}

            # Process the value based on depth
            parsed_value = self._parse_value(value)

            if (
                len(parts) == 4  # noqa: PLR2004
            ):  # Nested attribute like columns[n][search][value]
                nested_attribute = parts[3][:-1]

                # Create or update nested dictionary
                if column_attribute not in by_number[column_number]:
                    by_number[column_number][column_attribute] = {
                        nested_attribute: parsed_value
                    }
                else:
                    by_number[column_number][column_attribute][nested_attribute] = (
                        parsed_value
                    )
            else:  # Direct attribute like columns[n][data]
                by_number[column_number][column_attribute] = parsed_value

        return by_number

    def _convert_to_name_indexed(
        self, by_number: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Transform ``by_number`` from column-index-indexed to column-name-indexed
        structure.

        This makes lookups more intuitive by using column names rather than positions.

        Args:
            by_number: Dictionary mapping column indices to their attributes

        Returns:
            dict[str, Any]: Dictionary mapping column names to their attributes
                and values, structured for easy access by column name.

        """
        by_name = {}
        for column_data in by_number.values():
            # Skip columns without a data attribute
            if "data" not in column_data:
                continue

            # Use the 'data' attribute as the key
            column_name = column_data["data"]
            by_name[column_name] = column_data

        return by_name

    @lru_cache(maxsize=4)
    def searchable_columns(self) -> list[str]:
        """
        Get the list of column names that are marked as searchable.

        This method parses the column configuration to identify which columns
        should be included in global searches and per-column filtering.
        The result is cached for performance.

        Returns:
            list[str]: List of searchable column names

        """
        return [
            key
            for key, value in self.columns(self._querydict).items()
            if value["searchable"]
        ]

    def column_specific_searches(self) -> list[tuple[str, str]]:
        """
        Get a list of active per-column search filters.

        This method identifies columns that have search values specified
        in the DataTables request, which happens when a user enters a search
        term in a specific column's filter input.

        Returns:
            list[tuple[str, str]]: List of (column_name, search_value) pairs

        """
        return [
            (key, value["search"]["value"])
            for key, value in self.columns(self._querydict).items()
            if value["search"]["value"]
        ]

    def single_column_filter(
        self, qs: models.QuerySet, column: str, value: str
    ) -> models.QuerySet:
        """
        Apply filtering to a queryset based on a single column search.

        This method filters the queryset by a specific column value. It supports:

        1. Custom filtering via ``filter_COLUMNNAME_column`` methods
        2. Default ``icontains`` filtering for searchable columns

        Args:
            qs: The queryset to filter
            column: The column name to filter on
            value: The search value to filter by

        Returns:
            models.QuerySet: The filtered queryset

        Example:
            To implement custom filtering for a specific column:

            .. code-block:: python

                from django.db.models import QuerySet

                def filter_status_column(
                    self,
                    qs: QuerySet,
                    column: str,
                    value: str
                ) -> QuerySet:
                    if value.lower() == 'active':
                        return qs.filter(is_active=True)
                    elif value.lower() == 'inactive':
                        return qs.filter(is_active=False)
                    return qs

        """
        attr_name = f"filter_{column}_column"
        if hasattr(self, attr_name):
            qs = getattr(self, attr_name)(qs, column, value)
        elif column in self.searchable_columns():
            kwarg_name = f"{column}__icontains"
            qs = qs.filter(**{kwarg_name: value})
        return qs

    def search_query(self, qs: models.QuerySet, value: str) -> Q | None:
        """
        Build a Q object for performing global search across multiple columns.

        This method constructs a query that searches all searchable columns
        for the given value, using OR logic to match records that have the value
        in any searchable column.

        Args:
            qs: The queryset (not used in the default implementation)
            value: The search term to look for

        Returns:
            Q | None: A Django Q object representing the search, or None if no
               searchable columns exist

        """
        query: Q | None = None
        for column in self.searchable_columns():
            attr_name = f"search_{column}_column"
            if hasattr(self, attr_name):
                q = getattr(self, attr_name)(qs, column, value)
            else:
                kwarg_name = f"{column}__icontains"
                q = Q(**{kwarg_name: value})
            query = query | q if query else q
        return query

    def search(self, qs: models.QuerySet, value: str) -> models.QuerySet:
        """
        Apply a global search across all searchable columns.

        This method is called when a user enters a search term in the main
        dataTables.js search input. It applies the search across all searchable
        columns and returns distinct results.

        Args:
            qs: The queryset to search
            value: The search term

        Returns:
            models.QuerySet: The filtered queryset containing only matching records

        """
        query = self.search_query(qs, value)
        return qs.filter(query).distinct()

    def filter_queryset(self, qs: models.QuerySet) -> models.QuerySet:
        """
        Apply all filtering to the queryset based on dataTables.js parameters.

        This method handles both:

        1. Per-column searches specified by column-specific filters
        2. Global searches from the main dataTables.js search input

        Args:
            qs: The queryset to filter

        Returns:
            models.QuerySet: The filtered queryset

        """
        column_searches = self.column_specific_searches()
        if column_searches:
            for column, value in column_searches:
                qs = self.single_column_filter(qs, column, value)
        _value = self.request.GET.get("search[value]")
        if _value:
            qs = self.search(qs, _value)
        return qs

    def _render_column(self, row: Any, column: str) -> str:
        """
        Preprocess column names before rendering values.

        This method converts Django-style relationship traversal notation (`__`)
        to dot notation (`.`) for proper attribute access.

        Args:
            row: The model instance or dictionary for this row
            column: The column name, possibly using relationship notation

        Returns:
            str: The rendered column value

        """
        column = re.sub("__", ".", column)
        return super()._render_column(row, column)

    def render_column(self, row: Any, column: str) -> str:
        """
        Render a column value with custom rendering support.

        This method enables custom column rendering through convention-based
        method naming. If a method named ``render_COLUMNNAME_column`` exists, it
        will be called to render the column instead of the default implementation.

        Args:
            row: The model instance or dictionary for this row
            column: The column name

        Returns:
            str: The rendered column value

        Example:
            To customize rendering for a 'status' column:

            .. code-block:: python

                def render_status_column(self, row: Model, column: str) -> str:
                    status = row.status
                    if status == 'active':
                        return f'<span class="badge bg-success">{status}</span>'
                    return f'<span class="badge bg-secondary">{status}</span>'

        """
        attr_name = f"render_{column}_column"
        if hasattr(self, attr_name):
            return getattr(self, attr_name)(row, column)
        return super().render_column(row, column)
