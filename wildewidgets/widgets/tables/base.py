from __future__ import annotations

import random
from copy import deepcopy
from typing import Any

from django import template

from wildewidgets.views import WidgetInitKwargsMixin

from ..base import Widget
from .components import (
    DataTableColumn,
    DataTableFilter,
    DataTableForm,
    DataTableStyler,
)
from .views import DatatableAJAXView


class BaseDataTable(Widget, WidgetInitKwargsMixin, DatatableAJAXView):  # type: ignore[misc]
    """
    Base class for creating interactive `dataTables <https://datatables.net/>`_
    with sorting, filtering, and pagination.

    This class provides the foundation for building powerful data tables with
    features like:

    - Client-side or server-side processing
    - Column sorting and filtering
    - Pagination
    - Custom styling and formatting
    - Action buttons for row operations
    - Bulk actions through form submissions

    The `BaseDataTable` can operate in two modes:

    1. Synchronous mode: All data is loaded and processed in the browser
    2. Asynchronous mode: Data is loaded via AJAX from the server as needed

    Example:
        .. code-block:: python

            from wildewidgets import BaseDataTable

            class UserTable(BaseDataTable):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.add_column("username", "Username")
                    self.add_column("email", "Email")
                    self.add_column("date_joined", "Joined")

                def render_date_joined_column(self, row, column):
                    return row.date_joined.strftime("%Y-%m-%d")

    Args:
        *args: Positional arguments passed to the parent Widget class

    Keyword Args:
        title: The title of the table, displayed above the table controls
        width: CSS width for the table (default is "100%")
        height: CSS height for the table (optional)
        searchable: Whether to show a search input (default is True)
        paging: Whether to enable pagination (default is True)
        page_length: Number of rows per page (default is 25)
        small: Use smaller font and row height (default is False)
        buttons: Add export buttons (default is False)
        striped: Use alternating row colors (default is False)
        hide_controls: Hide pagination and search controls (default is False)
        table_id: Custom CSS ID for the table (random if None)
        sort_ascending: Default sort order for the table (default is True)
        data: Initial data to populate the table (optional, empty by default)
        form_actions: List of bulk actions for selected rows (optional)
        form_url: URL to submit form actions (optional)
        ajax_url_name: URL name for the AJAX endpoint (default is "wildewidgets_json")
        column_wrap_fields: List of fields to wrap in table controls (optional)
        is_async: If True, use AJAX to load data when the table is empty
        (default is True)
        **kwargs: Keyword arguments for parent Widget class initialization


    """

    #: The Django template file to use for rendering the table
    template_file: str = "wildewidgets/table.html"

    #: The URL name for the dataTables AJAX endpoint
    ajax_url_name: str = "wildewidgets_json"

    #: The header fields to wrap in the table controls
    column_wrap_fields: list[str] = []  # noqa: RUF012

    # dataTable specific configs

    #: How tall should we make the table?  Any CSS width string is valid.
    height: str | None = None
    #: How wide should we make the table?  Any CSS width string is valid.
    width: str | None = "100%"
    #: If ``True``, use smaller font and row height when rendering rows
    small: bool = False
    #: If ``True``, use different colors for even and odd rows
    striped: bool = False
    #: Show the search input?
    searchable: bool = True
    #: How many rows should we show on each page
    page_length: int = 25
    #: If ``True``, sort rows ascending; otherwise descending.
    sort_ascending: bool = True
    #: Hide our paging, page length and search controls
    hide_controls: bool = False

    #: The CSS id to assign to the table.  The id will be ``datatable_table_{table_id}``
    #: If this is ``None``, a random id will be generated.
    table_id: str | None = None

    #: If ``True``, add the dataTable "Copy", "CSV", "Export" and "Print" buttons
    buttons: bool = False

    #: Whole table form actions.  If this is not ``None``, add a first column with
    #: checkboxes to each row, and a form that allows you to choose bulk actions
    #: to perform on all checked rows.
    form_actions = None
    #: The URL to which to POST our form actions if :py:attr:`form_actions` is
    #: not ``None``
    form_url: str = ""
    #: If ``True``, use AJAX to load data when the table is empty
    is_async: bool = True

    def __init__(  # noqa: PLR0913
        self,
        *args,
        width: str | None = None,
        height: str | None = None,
        title: str | None = None,
        searchable: bool | None = True,
        paging: bool | None = True,
        page_length: int | None = None,
        small: bool | None = None,
        buttons: bool | None = None,
        striped: bool | None = None,
        hide_controls: bool | None = None,
        table_id: str | None = None,
        sort_ascending: bool | None = None,
        data: list[Any] | None = None,
        form_actions: Any = None,
        form_url: str | None = None,
        ajax_url_name: str | None = None,
        column_wrap_fields: list[str] | None = None,
        is_async: bool | None = None,
        **kwargs,
    ):
        self.width = width if width is not None else self.width
        self.height = height if height is not None else self.height
        self.title = title if title is not None else self.title
        self.searchable = searchable if searchable is not None else self.searchable
        self.page_length = page_length if page_length is not None else self.page_length
        self.small = small if small is not None else self.small
        self.buttons = buttons if buttons is not None else self.buttons
        self.striped = striped if striped is not None else self.striped
        self.hide_controls = (
            hide_controls if hide_controls is not None else self.hide_controls
        )
        #: These are options for dataTable itself and get set in the JavaScript
        #: constructor for the table.
        self.datatable_options: dict[str, Any] = {
            "width": self.width,
            "height": self.height,
            "title": self.title,
            "searchable": self.searchable,
            "paging": paging,
            "page_length": self.page_length,
            "small": self.small,
            "buttons": self.buttons,
            "striped": self.striped,
            "hide_controls": self.hide_controls,
        }
        #: The CSS id for this table
        self.table_id = table_id if table_id else self.table_id
        if self.table_id is None:
            self.table_id = str(random.randrange(0, 1000))  # noqa: S311
        self.table_name = f"datatable_table_{self.table_id}"
        # We have to do this this way instead of naming it above in the kwargs
        # because ``async`` is a reserved keyword
        self.async_if_empty: bool = is_async if is_async is not None else self.is_async
        #: A mapping of field name to column definition
        self.column_fields: dict[str, DataTableColumn] = {}
        #: A mapping of field name to column filter definition
        self.column_filters: dict[str, DataTableFilter] = {}
        #: A list of column styles to apply
        self.column_styles: list[DataTableStyler] = []
        self.data = data if data else []
        self.sort_ascending = (
            sort_ascending if sort_ascending is not None else self.sort_ascending
        )
        self.form_actions = (
            form_actions if form_actions else deepcopy(self.form_actions)
        )
        self.form_url = form_url if form_url else self.form_url
        self.ajax_url_name = ajax_url_name if ajax_url_name else self.ajax_url_name
        self.column_wrap_fields = (
            column_wrap_fields
            if column_wrap_fields
            else deepcopy(self.column_wrap_fields)
        )
        if self.has_form_actions():
            self.column_fields["checkbox"] = DataTableColumn(
                field="checkbox",
                verbose_name=" ",
                searchable=False,
                sortable=False,
            )
        super().__init__(*args, **kwargs)

    def get_column_number(self, name: str) -> int:
        """
        Get the numerical index of a column in the table by its name.

        This is useful when you need to reference columns in JavaScript operations
        or when configuring DataTables-specific functionality.

        Args:
            name: The field name of the column to find

        Returns:
            int: Zero-based index of the column in the table

        Raises:
            IndexError: If no column with the given name exists in the table

        """
        columns = list(self.column_fields.keys())
        if name in columns:
            return columns.index(name)
        msg = f'No column with name "{name}" is registered with this table'
        raise IndexError(msg)

    def has_form_actions(self) -> bool:
        """
        Check if this table has form actions defined.

        Form actions allow users to perform bulk operations on selected rows
        by checking the checkboxes and submitting the form.

        Returns:
            bool: True if form actions are defined, False otherwise

        """
        return self.form_actions is not None

    def get_form_actions(self) -> Any:
        """
        Get the list of form actions defined for this table.

        Returns:
            Any: The :py:attr:`form_actions` list or ``None`` if no actions are
                defined

        """
        return self.form_actions

    def add_form_action(self, action: Any) -> None:
        """
        Add a new form action to this table.

        Form actions appear in a dropdown when rows are selected via checkboxes.

        Args:
            action: The form action to add (usually a tuple of label and handler)

        """
        if not self.form_actions:
            self.form_actions = []
        self.form_actions.append(action)

    def add_column(
        self,
        field: str,
        verbose_name: str | None = None,
        searchable: bool = True,
        sortable: bool = True,
        align: str = "left",
        head_align: str = "left",
        visible: bool = True,
        wrap: bool = True,
    ) -> None:
        """
        Add a column to the table definition.

        This method defines a new column in the table. The table will look for a
        method named ``render_{field}_column`` to handle custom rendering of the
        column's cell values.

        Args:
            field: The name of the field/attribute to render in this column
            verbose_name: Display name for the column header (defaults to
                capitalized field name)
            searchable: Whether this column is included in global search
            sortable: Whether the table can be sorted by this column
            align: Horizontal alignment for cell content ("left", "right", "center")
            head_align: Horizontal alignment for the header cell ("left",
                "right", "center")
            visible: Whether the column is initially visible
            wrap: Whether to wrap content in this column

        Example:
            .. code-block:: python

                from wildewidgets import BaseDataTable

                table = BaseDataTable(
                    title="User List",
                    searchable=True,
                    paging=True,
                    page_length=10
                )

                table.add_column(
                    "created_at",
                    "Created",
                    align="right",
                    sortable=True
                )

        """
        self.column_fields[field] = DataTableColumn(
            field=field,
            verbose_name=verbose_name,
            searchable=searchable,
            sortable=sortable,
            align=align,
            head_align=head_align,
            visible=visible,
            wrap=wrap,
        )

    def add_filter(self, field: str, dt_filter: DataTableFilter) -> None:
        """
        Add a filter control for a specific column.

        Filters allow users to narrow down data based on column values.

        Args:
            field: The name of the field/column to filter
            dt_filter: A DataTableFilter instance defining the filter behavior

        Example:
            .. code-block:: python

                from wildewidgets import BaseDataTable, DataTableFilter

                table = BaseDataTable(
                    title="User List",
                    searchable=True,
                    paging=True,
                    page_length=10
                )

                table.add_filter(
                    "status",
                    DataTableFilter(
                        choices=[("active", "Active"), ("inactive", "Inactive")]
                    )
                )

        """
        self.column_filters[field] = dt_filter

    def remove_filter(self, field: str) -> None:
        """
        Remove a previously defined filter from a column.

        Args:
            field: The name of the field/column to remove the filter from

        """
        del self.column_filters[field]

    def add_styler(self, styler: DataTableStyler) -> None:
        """
        Add a style rule to the table.

        Stylers allow conditional formatting of cells based on their values
        or the values of other cells in the same row.

        Args:
            styler: A :py:class:`wildewidgets.DataTableStyler` instance defining
                the styling rule

        Example:
            .. code-block:: python

                from wildewidgets import BaseDataTable, DataTableStyler

                table = BaseDataTable(
                    title="User List",
                    searchable=True,
                    paging=True,
                    page_length=10
                )

                # Style the "status" column red when its value is "error"
                table.add_styler(
                    DataTableStyler(
                        test_cell="status",
                        test_value="error",
                        css_class="text-danger"
                    )
                )

        """
        styler.test_index = list(self.column_fields.keys()).index(styler.test_cell)
        if styler.target_cell:
            styler.target_index = list(self.column_fields.keys()).index(
                styler.target_cell
            )
        self.column_styles.append(styler)

    def build_context(self, **kwargs) -> dict[str, Any]:
        """
        Build the context for synchronous table rendering.

        This method adds the table's row data to the context for template rendering.
        Override this method to customize how data is prepared for the template.

        Args:
            **kwargs: The template context to update

        Returns:
            dict: The updated context with row data

        """
        kwargs["rows"] = self.data
        return kwargs

    def get_template_context_data(self, **kwargs) -> dict[str, Any]:
        """
        Prepare the complete context for table template rendering.

        This method builds the context dictionary with all necessary data for
        rendering the table template, including configuration, filters, headers,
        and data mode (async or sync).

        Args:
            **kwargs: Initial context values

        Returns:
            dict: Complete context dictionary for template rendering

        """
        kwargs = super().get_template_context_data(**kwargs)
        has_filters = False
        filters: list[tuple[DataTableColumn, DataTableFilter] | None] = []
        for key, item in self.column_fields.items():
            if key in self.column_filters:
                filters.append((item, self.column_filters[key]))
                has_filters = True
            else:
                filters.append(None)
        if self.data or not self.async_if_empty:
            kwargs = self.build_context(**kwargs)
            kwargs["async"] = False
        else:
            kwargs["async"] = True
        kwargs["header"] = self.column_fields
        kwargs["has_form_actions"] = self.has_form_actions()
        kwargs["filters"] = filters
        kwargs["stylers"] = self.column_styles
        kwargs["has_filters"] = has_filters
        kwargs["options"] = self.datatable_options
        table_id = self.table_id if self.table_id else str(random.randrange(0, 1000))  # noqa: S311
        kwargs["name"] = f"datatable_table_{table_id}"
        kwargs["sort_ascending"] = self.sort_ascending
        kwargs["column_wrap_fields"] = self.column_wrap_fields
        kwargs["tableclass"] = self.__class__.__name__
        if not self.data:
            kwargs["extra_data"] = self.get_encoded_extra_data()
        kwargs["form"] = DataTableForm(self)
        if "csrf_token" in kwargs:
            kwargs["csrf_token"] = kwargs["csrf_token"]
        kwargs["ajax_url_name"] = self.ajax_url_name
        return kwargs

    def get_content(self, **kwargs) -> str:
        """
        Render the table to HTML.

        This method generates the complete HTML for the table by rendering
        the template with the prepared context.

        Args:
            **kwargs: Additional context values to include

        Returns:
            str: The rendered HTML for the table

        """
        context = self.get_template_context_data(**kwargs)
        html_template = template.loader.get_template(self.template_file)  # type: ignore[attr-defined]
        return html_template.render(context)

    def __str__(self) -> str:
        """
        Return the string representation of the table.

        This method allows the table to be included directly in templates
        using the {{ table }} syntax.

        Returns:
            str: The rendered HTML for the table

        """
        return self.get_content()

    def add_row(self, **kwargs) -> None:
        """
        Add a row to the table's data.

        This method is used for synchronous tables to add data directly.

        Args:
            **kwargs: Field values as key-value pairs, where keys match column names

        Example:
            .. code-block:: python

                from wildewidgets import BaseDataTable

                table = BaseDataTable(
                    title="User List",
                    searchable=True,
                    paging=True,
                    page_length=10
                )

                table.add_row(
                    username="johndoe",
                    email="john@example.com",
                    date_joined="2023-01-15"
                )

        """
        row = []
        for field in self.column_fields:
            if field in kwargs:
                row.append(kwargs[field])
            else:
                row.append("")
        self.data.append(row)

    def render_checkbox_column(self, row: Any, column: str) -> str:  # noqa: ARG002
        """
        Render the checkbox column for form actions.

        This method generates the HTML for the checkbox in each row when
        form_actions are enabled. The checkbox uses the row's ID as its value.

        Args:
            row: The data object for the current row
            column: The column name (always "checkbox")

        Returns:
            str: HTML for the checkbox input

        """
        return f'<input type="checkbox" name="checkbox" value="{row.id}">'
