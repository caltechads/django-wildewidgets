from __future__ import annotations

from typing import Any


class DataTableColumn:
    """
    Defines a column configuration for a :py:class:`wildewidgets.DataTable`.

    This class stores the configuration for a single column in a ``DataTable``,
    including display options, behavior, and formatting settings.

    Example:
        .. code-block:: python

            from wildewidgets import DataTableColumn

            # Create a right-aligned numeric column that can be sorted
            column = DataTableColumn(
                field="amount",
                verbose_name="Amount ($)",
                searchable=True,
                sortable=True,
                align="right"
            )

    Args:
        field: Field name or identifier for the column

    Keyword Args:
        verbose_name: Human-readable name for the column header
            (defaults to capitalized field name)
        searchable: Whether this column is included in global searches
        sortable: Whether the table can be sorted by this column
        align: Horizontal alignment of cell content ("left", "right", "center")
        head_align: Horizontal alignment of the column header
            ("left", "right", "center")
        visible: Whether the column is visible in the table
        wrap: Whether to wrap text content in the column cells

    """

    def __init__(
        self,
        field: str,
        verbose_name: str | None = None,
        searchable: bool = False,
        sortable: bool = False,
        align: str = "left",
        head_align: str = "left",
        visible: bool = True,
        wrap: bool = True,
    ):
        self.field = field
        self.verbose_name = verbose_name if verbose_name else self.field.capitalize()
        self.searchable = searchable
        self.sortable = sortable
        self.align = align
        self.head_align = head_align
        self.visible = visible
        self.wrap = wrap


class DataTableFilter:
    """
    Defines a filter control for a :py:class:`wildewidgets.DataTable` column.

    This class represents a UI control for filtering data in a specific column,
    typically displayed as a dropdown list of options.

    Example:
        .. code-block:: python

            from wildewidgets import DataTableFilter

            # Create a status filter with custom options
            filter = DataTableFilter(
                header="Filter by Status",
            )
            filter.add_choice("Active", "active")
            filter.add_choice("Inactive", "inactive")
            filter.add_choice("Pending", "pending")

            # Add the filter to the table
            table.add_filter("status", filter)

    Keyword Args:
        header: Optional header content for the filter

    """

    def __init__(self, header: Any | None = None) -> None:
        self.header = header
        self.choices: list[tuple[str, str]] = [("Any", "")]

    def add_choice(self, label: str, value: str) -> None:
        """
        Add a filter option to the choices list.

        Args:
            label: The human-readable label displayed in the UI
            value: The value used for filtering when this option is selected

        """
        self.choices.append((label, value))


class DataTableStyler:
    """
    Defines conditional styling rules for DataTable cells or rows.

    This class allows you to apply CSS classes to table cells or rows
    based on the content of a specific cell. It's used for conditional
    formatting, like highlighting negative values in red or flagging
    certain status values.

    Example:
        .. code-block:: python

            from wildewidgets import BaseDataTable, DataTableStyler, DataTableColumn

            # Style the status column with "text-danger" when value is "error"
            styler = DataTableStyler(
                is_row=False,
                test_cell="status",
                cell_value="error",
                css_class="text-danger"
            )

            # Style the entire row with "table-warning" when status is "pending"
            row_styler = DataTableStyler(
                is_row=True,
                test_cell="status",
                cell_value="pending",
                css_class="table-warning"
            )

            table = BaseDataTable(
                title="My Data Table",
                columns=[
                    DataTableColumn(field="name", verbose_name="Name"),
                    DataTableColumn(field="status", verbose_name="Status"),
                ],
            )

            table.add_styler(styler)
            table.add_styler(row_styler)

    Args:
        is_row: Whether to apply styling to the entire row (True)
            or just a cell (False)
        test_cell: The name of the column to test for the condition
        cell_value: The value to compare against for the condition
        css_class: The CSS class to apply when the condition is met

    Keyword Args:
        target_cell: The name of the column to style
            (if None, uses :py:attr:`test_cell`)


    """

    def __init__(
        self,
        is_row: bool,
        test_cell: str,
        cell_value: Any,
        css_class: str,
        target_cell: str | None = None,
    ):
        self.is_row = is_row
        self.test_cell = test_cell
        self.cell_value = cell_value
        self.css_class = css_class
        self.target_cell = target_cell
        self.test_index = 0
        self.target_index = 0


class DataTableForm:
    """
    Provides form handling for bulk actions in a DataTable.

    This class integrates form functionality into a DataTable, allowing
    users to select multiple rows using checkboxes and perform actions
    on the selected rows, such as delete, approve, or export.

    Note:
        This class is created automatically by the
        :py:class:`wildewidgets.DataTable` or its subclasses when
        :py:attr:`wildewidgets.DataTable.form_actions` are defined.

        You typically do not need to instantiate this class directly.

        The form is only visible if the table has
        :py:attr:`wildewidgets.DataTable.form_actions` defined.  Form actions and
        URL are retrieved from the table instance.

    Args:
        table: The DataTable instance this form belongs to

    """

    def __init__(self, table: Any):
        if table.has_form_actions():
            self.is_visible: bool = True
        else:
            self.is_visible = False
        self.actions = table.get_form_actions()
        self.url = table.form_url
