from copy import deepcopy
import random
from typing import Any, Dict, List, Optional

from django import template
from wildewidgets.views import WidgetInitKwargsMixin

from ..base import Widget

from .components import (
    DataTableColumn,
    DataTableFilter,
    DataTableForm,
    DataTableStyler
)
from .views import DatatableAJAXView


class BaseDataTable(
    Widget,
    WidgetInitKwargsMixin,
    DatatableAJAXView
):
    """
    This is the base class for all other dataTable classes.

    Keyword Args:
        width: The table width as a CSS specifier, e.g. "``100%``", "``500px``"
        height: The table height as a CSS specifier, e.g. "``500px``"
        title: The table title
        searchable: Whether the table is searchable
        paging: Whether the table is paged
        page_length: How many rows should we show on each page?
        small: If ``True``, use smaller font and row height when rendering rows
        buttons: If ``True``, add the dataTable "Copy", "CSV", "Export" and "Print" buttons
        striped: If ``True``, use different colors for even and odd rows
        table_id: The table CSS id
        async: If ``True`` the table will use AJAX to do its work via the ``/wildewidgets_json``.
            If ``False`` all data will be loaded into the table at render time.
        data: The table data
        sort_ascending: If ``True``, sort the rows in the table ascending; if ``False``, sort
            descending.
        action_button_size: The size of the action button. Defaults to 'normal'.
            Valid values are ``normal``, ``sm``, ``lg``.
    """

    template_file: str = 'wildewidgets/table.html'

    #: The URL name for the dataTables AJAX endpoint
    ajax_url_name: str = 'wildewidgets_json'

    # dataTable specific configs

    #: How tall should we make the table?  Any CSS width string is valid.
    height: Optional[str] = None
    #: How wide should we make the table?  Any CSS width string is valid.
    width: Optional[str] = '100%'
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
    table_id: Optional[str] = None

    #: If ``True``, add the dataTable "Copy", "CSV", "Export" and "Print" buttons
    buttons: bool = False

    #: Whole table form actions.  If this is not ``None``, add a first column with
    #: checkboxes to each row, and a form that allows you to choose bulk actions
    #: to perform on all checked rows.
    form_actions = None
    #: The URL to which to POST our form actions if :py:attr:`form_actions` is
    #: not ``None``
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
        small: bool = None,
        buttons: bool = None,
        striped: bool = None,
        hide_controls: bool = None,
        table_id: str = None,
        sort_ascending: bool = None,
        data: List[Any] = None,
        form_actions: Any = None,
        form_url: str = None,
        ajax_url_name: str = None,
        **kwargs
    ):
        self.width = width if width is not None else self.width
        self.height = height if height is not None else self.height
        self.title = title if title is not None else self.title
        self.searchable = searchable if searchable is not None else self.searchable
        self.page_length = page_length if page_length is not None else self.page_length
        self.small = small if small is not None else self.small
        self.buttons = buttons if buttons is not None else self.buttons
        self.striped = striped if striped is not None else self.striped
        self.hide_controls = hide_controls if hide_controls is not None else self.hide_controls
        #: These are options for dataTable itself and get set in the JavaScript
        #: constructor for the table.
        self.options = {
            'width': self.width,
            'height': self.height,
            "title": self.title,
            "searchable": self.searchable,
            "paging": paging,
            "page_length": self.page_length,
            "small": self.small,
            "buttons": self.buttons,
            "striped": self.striped,
            "hide_controls": self.hide_controls
        }
        #: The CSS id for this table
        self.table_id = table_id if table_id else self.table_id
        if self.table_id is None:
            self.table_id = random.randrange(0, 1000)
        self.table_name = f'datatable_table_{self.table_id}'
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
        self.form_actions = form_actions if form_actions else deepcopy(self.form_actions)
        self.form_url = form_url if form_url else self.form_url
        self.ajax_url_name = ajax_url_name if ajax_url_name else self.ajax_url_name
        if self.has_form_actions():
            self.column_fields['checkbox'] = DataTableColumn(
                field='checkbox',
                verbose_name=' ',
                searchable=False,
                sortable=False
            )
        super().__init__(*args, **kwargs)

    def get_column_number(self, name: str) -> int:
        """
        Return the dataTables column number for the column named ``name``.  You
        might need this if you want to pass it to javascript that will work on
        that column.

        Args:
            name: the name of the column

        Raises:
            IndexError: no column named ``name`` exists in this table

        Returns:
            The 0-offset column number
        """
        columns = list(self.column_fields.keys())
        if name in columns:
            return columns.index(name)
        raise IndexError(f'No column with name "{name}" is registered with this table')

    def has_form_actions(self) -> bool:
        return self.form_actions is not None

    def get_form_actions(self):
        return self.form_actions

    def add_form_action(self, action):
        self.form_actions.append(action)

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
            head_align: horizontal alignment for the header for this column:
                ``left``, ``right``, ``center``
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
        kwargs["ajax_url_name"] = self.ajax_url_name
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
