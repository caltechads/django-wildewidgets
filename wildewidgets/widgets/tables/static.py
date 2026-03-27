import uuid

from ..base import Block

# -----------------------------------------------------------------------------
# Widgets
# -----------------------------------------------------------------------------


class StaticTableRowWidget(Block):
    """
    Simple static table row widget.  This widget is used to create a row in a
    :class:`~workshop_admin.core.wildewidgets.StaticTableWidget`.

    Args:
        cells: the cells to add to the row
        cell_tag: the HTML tag for the cells
        cell_css_class: the CSS class for the cells
        **kwargs: additional keyword arguments to pass to the block

    """

    #: The HTML tag for the row
    tag: str = "tr"
    #: The HTML tag for the cells
    cell_tag: str = "td"

    def __init__(
        self,
        cells: list[str | Block],
        cell_tag: str | None = None,
        cell_css_class: str | None = None,
        **kwargs,
    ) -> None:
        if cell_tag is not None:
            self.cell_tag = cell_tag
        rendered_cells: list[Block] = []
        for cell in cells:
            if isinstance(cell, Block) and cell.tag == self.cell_tag:
                rendered_cells.append(cell)
                continue
            rendered_cells.append(
                Block(cell, tag=self.cell_tag, css_class=cell_css_class)
            )
        super().__init__(*rendered_cells, **kwargs)


class StaticTableWidget(Block):
    """
    Simple static table widget.  This differs from the
    :class:`~wildewidgets.DataTable` type widgets in that it does not use
    dataTables.js and is therefore simpler for small lists of data.

    It offers a sorting mechanism by clicking on the "Sort" button in the heading
    of the column.  The table is sorted by the text content of the cells in the
    column that the button is in.  If every cell in that column is numeric
    (optional minus, digits, optional decimal), the column is sorted numerically;
    otherwise locale-aware alphabetical sort is used.  Empty cells in numeric
    columns sort last (ascending) or first (descending).

    Examples:
        With constructor arguments:

        .. code-block:: python

            from wildewidgets import StaticTableWidget

            table = StaticTableWidget(
                headings=["Name", "Age", "City"],
                rows=[["John", 25, "New York"], ["Jane", 30, "Los Angeles"]]
            )

            print(table)

        With constructor overrides:

        .. code-block:: python

            from wildewidgets import StaticTableWidget

            class MyStaticTableWidget(StaticTableWidget):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.add_heading("Name")
                    self.add_heading("Age")
                    self.add_heading("City")
                    self.add_row(["John", 25, "New York"])
                    self.add_row(["Jane", 30, "Los Angeles"])

            table = MyStaticTableWidget()
            print(table)

        With method calls:

        .. code-block:: python

            from wildewidgets import StaticTableWidget

            table = StaticTableWidget()
            table.add_heading("Name")
            table.add_heading("Age")
            table.add_heading("City")
            table.add_row(["John", 25, "New York"])
            table.add_row(["Jane", 30, "Los Angeles"])

            print(table)


        .. code-block:: python

            from wildewidgets import StaticTableWidget
            table = StaticTableWidget(
                headings=["Name", "Age", "City"],
                rows=[["John", 25, "New York"], ["Jane", 30, "Los Angeles"]]
            )
            table.add_heading("Country")
            table.add_heading("Occupation")
            table.add_heading("City"sjj
            table.add_row(
                 ["John", 25, "New York", "United States", "Software Engineer"]
            )
            table.add_row(
                ["Jane", 30, "Los Angeles", "United States", "Software Engineer"]
            )

            print(table)


    Keyword Args:
        headings: the headings for the table
        rows: the rows for the table
        cell_css_class: the CSS class for the cells
        **kwargs: additional keyword arguments to pass to the block

    """

    #: The HTML tag for the table
    tag: str = "table"
    #: The HTML name for the widget for CSS styling and JavaScript
    name: str = "static-table"

    @property
    def script(self) -> str:
        """
        A JavaScript script to sort the table by clicking on a button in the
        headings.

        Iniitially, the table is sorted in the order they are listed in the data
        source.

        It draws a button in the ``<th>`` elements named "Sort" with the current
        sort order represented by an arrow (if we are sorting) or a blank (if we
        are not sorting).  When the button is clicked, the table is sorted by
        the opposite of the current sort order or ascending (if no sort order is
        set), and the button text is updated to the opposite of the selected
        sort order.

        Note:
            The table is sorted by the text content of the cells in the column
            that the button is in.  If every cell in that column is numeric
            (optional minus, digits, optional decimal), the column is sorted
            numerically; otherwise locale-aware alphabetical sort is used.
            Empty cells in numeric columns sort last (ascending) or first
            (descending).

        Args:
            self: the widget instance

        Returns:
            A string of JavaScript code to sort the table by clicking on the headings.

        """
        sort_button = '<button class="btn btn-link btn-sm" style="font-size: 0.8em;">Sort</button>'  # noqa: E501
        return f"""
        document.addEventListener("DOMContentLoaded", function() {{
            var table = document.querySelector('table#{self._css_id}');
            // Add the up and down arrows to the headings.
            var headings = table.querySelectorAll('thead th');
            headings.forEach(function(heading) {{
                heading.innerHTML = heading.innerHTML + '{sort_button}';
            }});
            function isNumericColumn(rows, colIdx) {{
                var numericPattern = /^-?\\d*\\.?\\d+$/;
                for (var i = 0; i < rows.length; i++) {{
                    var cell = rows[i].cells[colIdx];
                    if (!cell) return false;
                    var text = (cell.textContent || '').trim();
                    if (text !== '' && !numericPattern.test(text)) return false;
                }}
                return true;
            }}
            function compareCells(aVal, bVal, numeric, asc) {{
                if (numeric) {{
                    var na = parseFloat(aVal);
                    var nb = parseFloat(bVal);
                    var aEmpty = (aVal.trim() === '') || isNaN(na);
                    var bEmpty = (bVal.trim() === '') || isNaN(nb);
                    if (aEmpty && bEmpty) return 0;
                    if (aEmpty) return asc ? 1 : -1;
                    if (bEmpty) return asc ? -1 : 1;
                    return asc ? (na - nb) : (nb - na);
                }}
                return asc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
            }}
            if (table) {{
                table.addEventListener('click', function(event) {{
                    var target = event.target;
                    if (target.tagName === 'BUTTON') {{
                        var columnIndex = target.parentElement.cellIndex;
                        var is_ascending = target.textContent.includes('↓');
                        var rows = Array.from(table.querySelectorAll('tbody tr'));
                        var numeric = isNumericColumn(rows, columnIndex);
                        if (!is_ascending) {{
                            rows.sort(function(a, b) {{
                                var aText = (a.cells[columnIndex].textContent || '').trim();
                                var bText = (b.cells[columnIndex].textContent || '').trim();
                                return compareCells(aText, bText, numeric, true);
                            }});
                        }} else {{
                            rows.sort(function(a, b) {{
                                var aText = (a.cells[columnIndex].textContent || '').trim();
                                var bText = (b.cells[columnIndex].textContent || '').trim();
                                return compareCells(aText, bText, numeric, false);
                            }});
                        }}
                        var tbody = table.querySelector('tbody');
                        tbody.innerHTML = '';
                        rows.forEach(function(row) {{
                            tbody.appendChild(row);
                        }});
                        // update the button text to the opposite of the current
                        // sort order
                        target.textContent = "Sort " + (!is_ascending ? '↓' : '↑');
                        // Set the buttons in the other columns to no sort
                        var otherColumns = table.querySelectorAll('thead th');
                        otherColumns.forEach(function(column) {{
                            if (column !== target.parentElement) {{
                                column.querySelector('button').textContent = 'Sort';
                            }}
                        }});
                    }}
                }});
            }}
        }});
        """  # noqa: E501, S608

    @script.setter
    def script(self, value: str) -> None:
        self._script = value

    def __init__(
        self,
        headings: list[str | Block] | None = None,
        rows: list[list[str | Block]] | None = None,
        cell_css_class: str | None = None,
        **kwargs,
    ) -> None:
        if headings is not None and rows is not None:
            assert len(headings) == len(rows[0]), (  # noqa: S101
                "Headings and rows must have the same length"
            )
        super().__init__(css_class="table table-sm mb-0", **kwargs)
        self.headings = headings or []
        self.rows = rows or []
        self.header = Block(tag="thead")
        self.body = Block(tag="tbody")
        self.cell_css_class = cell_css_class

        if self.headings:
            for heading in self.headings:
                self.header.add_block(
                    Block(heading, tag="th", css_class=self.cell_css_class)
                )
        for row in self.rows:
            self.body.add_block(
                StaticTableRowWidget(row, cell_css_class=self.cell_css_class)
            )

        if self.headings:
            self.add_block(self.header)
        if self.rows:
            self.add_block(self.body)

        if not self._css_id:
            self._css_id = f"static-table-{uuid.uuid4()}"

    def add_heading(self, heading: str | Block) -> None:
        """
        Add a single heading to the table.  Do this before adding any rows.

        Args:
            heading: the heading to add to the table

        """
        self.header.add_block(Block(heading, tag="th", css_class=self.cell_css_class))
        if self.header not in self.blocks:
            self.add_block(self.header)

    def add_row(self, row: list[str | Block]) -> None:
        """
        Add a single row to the table.  Do this after adding headings.
        """
        self.body.add_block(
            StaticTableRowWidget(row, cell_css_class=self.cell_css_class)
        )
        if self.body not in self.blocks:
            self.add_block(self.body)
