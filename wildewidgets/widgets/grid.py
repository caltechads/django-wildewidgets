from __future__ import annotations

import re
from copy import deepcopy
from functools import partial
from typing import Any, Final, cast

from .base import Block


class Column(Block):
    """
    Implements a ``col`` from the `Bootstrap Grid system
    <https://getbootstrap.com/docs/5.2/layout/grid/>`_.

    This is primarily meant to be used with :py:class:`Row`, but you can
    actually use :py:class:`Column` objects outside of a :py:class:`Row`.  This
    allows you to specify a particular width for the block within a page.  See
    `Boostrap: Columns, Standalone Column Classes
    <https://getbootstrap.com/docs/5.2/layout/columns/#standalone-column-classes>`_.

    Example:
        .. code-block:: python

            from wildewidgets import Column, Block

            col = Column(
                Block("This goes at the top of the column", css_class="mb-2"),
                Block("This goes at the bottom of the column"),
                base_width=6,
                viewport_widths={"md": "4", "lg": "3"},
                alignment="center",
                self_alignment="center"
            )

    Args:
        *blocks: a list of :py:class:`Block` objects or string to add to this column

    Keyword Args:
        base_width: the base width of this block for all viewports.  This will
            be converted to a ``col-{base_width}`` CSS class.  If this is not
            supplied and :py:attr:`base_width` is ``None``, add ``col`` as our
            CSS class.
        viewport_widths: a dict where the keys are Bootstrap viewport sizes (e.g.
            ``sm``, ``xl``) and the values are column widths, again between 1
            and 12 inclusive, or "auto".  These will be converted to CSS classes
            that look like ``col-{viewport}-{width}``
        alignment: how to align items within this column.  Valid choices: ``start``,
            ``center``, ``end``, ``between``, ``around``, ``evenly``.  See
            `Bootstrap: Flex, justify content
            <https://getbootstrap.com/docs/5.2/utilities/flex/#justify-content>`_.
            If not supplied here and :py:attr:`alignment` is ``None``, do
            whatever aligment Bootstrap does by default.
        self_alignment: how to align this column vertically within its
            containing row.  Valid choices: ``start``, ``end``, ``center``  See
            `Bootstrap Columns
            <https://getbootstrap.com/docs/5.2/layout/columns/#alignment>`_

    Raises:
        ValueError: there was a problem validating one of our settings

    """

    #: The minimum and maximum column widths, as per Bootstrap
    COL_MIN_WIDTH: Final[int] = 1
    COL_MAX_WIDTH: Final[int] = 12

    #: The valid column content alignments
    ALIGNMENTS: Final[list[str]] = [
        "start",
        "center",
        "end",
        "between",
        "around",
        "evenly",
    ]
    #: The valid self vertical alignments with our row
    SELF_ALIGNMENTS: Final[list[str]] = ["start", "center", "end"]

    #: A column width between 1 and 12 inclusive.  This is the base width
    #: for all viewports
    base_width: int | None = None
    #: A dict where the keys are Bootstrap viewport sizes (e.g.  #: ``sm``,
    #: ``xl``) and the values are column widths, again between 1 and 12
    #: inclusive, or "auto"
    viewport_widths: dict[str, str] = {}  # noqa: RUF012
    #: How to align items within this column.  Valid choices: ``start``,
    #: ``center``, ``end``, ``between``, ``around``, ``evenly``.  See `Bootstrap: Flex,
    #: justify content <https://getbootstrap.com/docs/5.2/utilities/flex/#justify-content>`_.
    #: If not supplied here and :py:attr:`alignment` is ``None``, do whatever aligment
    #: Bootstrap does by default.
    alignment: str | None = None
    #: How to align this column vertically within its containing row.  Valid
    #: choices: ``start``, ``end``, ``center``.  See `Bootstrap: Columns,
    #: Alignment : <https://getbootstrap.com/docs/5.2/layout/columns/#alignment>`_
    self_alignment: str | None = None

    def __init__(
        self,
        *blocks: Block,
        base_width: int | None = None,
        viewport_widths: dict[str, str] | None = None,
        alignment: str | None = None,
        self_alignment: str | None = None,
        **kwargs: Any,
    ):
        self.base_width = base_width if base_width else self.base_width
        self.viewport_widths = (
            viewport_widths if viewport_widths else deepcopy(self.viewport_widths)
        )
        self.alignment = alignment if alignment else self.alignment
        self.self_alignment = self_alignment if self_alignment else self.self_alignment
        self.check_widths()
        self.check_alignments()
        super().__init__(*blocks, **kwargs)
        if self.base_width:
            self.add_class(f"col-{self.base_width}")
        elif self.viewport_widths:
            self.add_class("col-12")
        else:
            self.add_class("col")
        for viewport, w in cast("dict[str, str]", self.viewport_widths).items():
            self.add_class(f"col-{viewport}-{w}")
        if self.alignment or self.self_alignment:
            self.add_class("d-flex")
        if self.alignment:
            self.add_class(f"justify-content-{self.alignment}")
        if self.self_alignment:
            self.add_class(f"align-self-{self.self_alignment}")

    def check_widths(self) -> None:
        """
        Validate our supplied ``width`` and ``viewport_widths`` settings to
        ensure widths for every viewport are between 0 and 12 inclusive, or (in
        the case of viewport specific widths).

        Raises:
            ValueError: a width was out of range

        """
        # TODO: validate viewport names also
        width: str | int
        if self.base_width:
            try:
                width = int(self.base_width)
            except ValueError as exc:
                msg = f'Invalid width "{self.base_width}".  Width must be an integer.'
                raise ValueError(msg) from exc
            else:
                if width and (width < 1 or width > self.COL_MAX_WIDTH):
                    msg = (
                        f"Invalid width {self.base_width}.  Width must be 0 > "
                        "width <= 12"
                    )
                    raise ValueError(msg)
        if self.viewport_widths:
            for viewport, width in self.viewport_widths.items():
                try:
                    _width = int(width)
                except ValueError as e:  # noqa: PERF203
                    if _width != "auto":
                        msg = (
                            f'Invalid width "{_width}" for viewport "{viewport}".  '
                            'Width must be either "auto" or, an integer 0 > width <= 12'
                        )
                        raise ValueError(msg) from e
                else:
                    if _width and (
                        _width < self.COL_MIN_WIDTH or _width > self.COL_MAX_WIDTH
                    ):
                        msg = (
                            f'Invalid width {width} for viewport "{viewport}".  Width '
                            "must be an integer 0 > width <= 12"
                        )
                        raise ValueError(msg)

    def check_alignments(self) -> None:
        """
        Check that our supplied ``alignment`` and ``self_alignment``  settings
        to ensure they are valid values from :py:attr:`ALIGNMENTS` and
        :py:attr:`SELF_ALIGNMENTS`, respectively.

        Raises:
            ValueError: an alignment was not valid

        """
        if self.alignment and self.alignment not in self.ALIGNMENTS:
            msg = (
                f"Invalid alignment: {self.alignment}.  Alignment must be one of "
                f"{', '.join(self.ALIGNMENTS)}"
            )
            raise ValueError(msg)
        if self.self_alignment and self.self_alignment not in self.SELF_ALIGNMENTS:
            msg = (
                f"Invalid self_alignment: {self.self_alignment}.  "
                f"Alignment must be one of {', '.join(self.SELF_ALIGNMENTS)}"
            )
            raise ValueError(msg)


class Row(Block):
    """
    Implements a ``row`` from the `Bootstrap Grid system
    <https://getbootstrap.com/docs/5.2/layout/grid/>`_.

    As columns are added to this Row, helper methods are also added
    to this :py:class:`row` instance, named for the :py:attr:`Column.name`
    of the column.  See :py:meth:`_add_helper_method` for details on how
    the helper methods will be named.

    Example:
        .. code-block:: python

            from wildewidgets import Row, Column, Block

            sidebar = Column(
                Block("This is in the sidebar"),
                name='sidebar',
                width=3
            )
            main = Column(
                Block("This is in the main content area"),
                name='main'
            )
            row = Row(
                sidebar,
                main,
                horizontal_alignment='center',
                vertical_alignment='center'
            )

    Args:
        *columns: one or more :py:class:`Column` objects

    Keyword Args:
        horizontal_alignment: the horizontal alignment for the columns in this
            row.  See `Bootstrap: Columns, Horizontal Alignment
            <https://getbootstrap.com/docs/5.2/layout/columns/#horizontal-alignment>`_.
            Valid choices: ``start``, ``center``, ``end``, ``around``, ``between``,
            ``evenly``.
        vertical_alignment: the vertical alignment for the columns in this
            row.  See `Bootstrap: Columns, Vertical Alignment
            <https://getbootstrap.com/docs/5.2/layout/columns/#vertical-alignment>`_.
            Valid choices: ``start``, ``center``, ``end``.

    Raises:
        ValueError: there was a problem validating one of our alignments

    """

    HORIZONTAL_ALIGNMENT: Final[list[str]] = [
        "start",
        "center",
        "end",
        "around",
        "between",
        "evenly",
    ]
    VERTICAL_ALIGNMENT: Final[list[str]] = ["start", "center", "end"]

    block: str = "row"

    #: A list of :py:class:`Column` blocks to add to the this row.
    #: This is List[Block] here so people can specify their own Column-like classes
    columns: list[Block] = []  # noqa: RUF012
    #: the horizontal alignment for the columns in this  row.  See
    #: `Bootstrap: Columns, Horizontal Alignment
    #: <https://getbootstrap.com/docs/5.2/layout/columns/#horizontal-alignment>`_
    horizontal_alignment: str | None = None
    #: the vertical alignment for the columns in this  row.  See
    #: `Bootstrap: Columns, Vertical Alignment
    #: <https://getbootstrap.com/docs/5.2/layout/columns/#vertical-alignment>`_
    vertical_alignment: str | None = None

    def __init__(
        self,
        *columns: Block,
        horizontal_alignment: str | None = None,
        vertical_alignment: str | None = None,
        **kwargs: Any,
    ):
        self.horizontal_alignment = (
            horizontal_alignment if horizontal_alignment else self.horizontal_alignment
        )
        self.vertical_alignment = (
            vertical_alignment if vertical_alignment else self.vertical_alignment
        )
        self.check_alignments()
        self.columns: list[Block] = list(columns)
        self.columns_map: dict[str, Block] = {}
        for i, column in enumerate(self.columns):
            name = column._name if column._name else f"column-{i + 1}"
            self.columns_map[name] = column
            self._add_helper_method(name)
        super().__init__(**kwargs)

    def check_alignments(self) -> None:
        """
        Check that our supplied ``horizontal_alignment`` and
        ``verttical_alignment`` settings to ensure they are valid values from
        :py:attr:`HORIZONTALALIGNMENTS` and :py:attr:`VERTICAL_ALIGNMENTS`,
        respectively.

        Raises:
            ValueError: an alignment was not valid

        """
        if (
            self.horizontal_alignment
            and self.horizontal_alignment not in self.HORIZONTAL_ALIGNMENT
        ):
            msg = (
                f'"{self.horizontal_alignment}" is not a valid horizontal alignment.  '
                f"Must be one of {', '.join(self.HORIZONTAL_ALIGNMENT)}"
            )
            raise ValueError(msg)
        if (
            self.vertical_alignment
            and self.vertical_alignment not in self.VERTICAL_ALIGNMENT
        ):
            msg = (
                f'"{self.vertical_alignment}" is not a valid vertical alignment.  '
                f"Must be one of {', '.join(self.VERTICAL_ALIGNMENT)}"
            )
            raise ValueError(msg)

    @property
    def column_names(self) -> list[str]:
        """
        Return the list of :py:attr:`Column.name` attributes of all of our
        columns.

        Returns:
            A list of column names.

        """
        return list(self.columns_map.keys())

    def _add_helper_method(self, name: str) -> None:
        """
        Add a method to this :py:class:`Row` object like so::

            def add_to_{column_name}(widget: Widget) -> None:
                ...

        This new method will allow you to add a widget to the column with name
        ``{column_name}`` directly without having to use
        :py:meth:`add_to_column`.

        Example:
            .. code-block:: python

                from wildewidgets.widgets import Row, Column, Block

                sidebar = Column(name='sidebar', width=3)
                main = Column(name='main')
                row = Row(columns=[sidebar, main])

            You can now add widgets to the sidebar column like so:

            .. code-block:: python

                widget = Block('foo')
                row.add_to_sidebar(widget)

        Args:
            name: the name of the column

        """
        name = re.sub("-", "_", name)
        setattr(self, f"add_to_{name}", partial(self.add_to_column, name))

    def add_column(self, column: Column) -> None:
        """
        Add a column to this row to the right of any existing columns.

        Note:
            A side effect of adding a column is to add a method to this
            :py:class:`Row` object like so:


            .. code-block:: python

                def add_to_{column_name}(widget: Widget) -> None:

            where ``{column_name}`` is either:

            * the value of ``column.name``, if that is not the default name
            * ``column-{n}`` where ``n`` is the number of columns in this row,
                starting with 1.

        Args:
            column: the column to add

        """
        if column._name:
            name: str = column._name
        else:
            name = f"column-{len(self.columns)}"
        self.add_block(column)
        self.columns.append(column)
        self.columns_map[name] = column
        self._add_helper_method(name)

    def add_to_column(self, identifier: int | str, block: Block) -> None:
        """
        Add ``widget`` to the column named ``identifier`` at the bottom of any
        other widgets in that column.

        Note:
            If ``identifier`` is an int, ``identifier`` should be 1-offset, not
            0-offset.

        Args:
            identifier: either a column number (left to right, starting with 1),
                or a column name
            block: the :py:class:`Block` subclass to append to this col

        """
        if isinstance(identifier, int):
            identifier = f"column-{identifier}"
        self.columns_map[identifier].add_block(block)


class TwoColumnLayout(Row):
    """
    A convenience widget that implements a two column ``row`` from the
    `Bootstrap Grid system <https://getbootstrap.com/docs/5.2/layout/grid/>`_
    with two named columns: ``left`` and ``right``.

    On viewports less than size ``md``, both columns will take up the entire width
    of the page (so that we look readable on portrait phones).

    Set the column widths for viewport ``md`` and above, define
    ``left_column_width`` as a class attribute or keyword argument, where 0 <
    ``left_column_width`` <= 12.  The default is to make the two columns
    equal widths.

    Examples:
        .. code-block:: python

            from wildewidgets import TwoColumnLayout, Block

            left_blocks = [Block('One', name='one'), Block('Two', name='two')]
            right_blocks = [Block('Three', name='three'), Block('Four', name='four')]
            layout = TwoColumnLayout(
                left_column_width=3,
                left_column_widgets=left_blocks,
                right_column_widgets=right_blocks
            )

    To create a two column layout with no blocks in either column:

        .. code-block:: python

            from wildewidgets import TwoColumnLayout

            layout = TwoColumnLayout(left_column_width=3)

    To create a two column layout with blocks in each column:

        .. code-block:: python

            from wildewidgets import TwoColumnLayout, Block

            layout = TwoColumnLayout(
                left_column_width=3,
                left_column_widgets=[
                    Block('One', name='one'), Block('Two', name='two')
                ],
                right_column_widgets=[
                    Block('Three', name='three'), Block('Four', name='four')
                ]
            )

    To add a block to a column after creating the ``TwoColumnLayout``:

        .. code-block:: python

            from wildewidgets import TwoColumnLayout, Block

            layout = TwoColumnLayout(left_column_width=3)
            layout.add_to_left_column(Block('One', name='one'))
            layout.add_to_right_column(Block('Two', name='two'))
            layout.add_to_left_column(Block('Three', name='three'))
            layout.add_to_right_column(Block('Four', name='four'))

    Keyword Args:
        left_column_width: the width of the left column, where 0 <
            ``left_column_width`` <= 12.  The right column will have its width set
            automatically based on this.
        left_column_widgets: A list of blocks to add to the left column
        right_column_widgets: A list of blocks to add to the right column

    """

    #: The name of this block
    name: str = "two-column"

    #: The width of the left column, where 0 < width <= 12.  The
    #: right column will have its width set automatically based on this.
    left_column_width: int = 6
    #: A list of blocks to add to the left column
    left_column_widgets: list[Block] = []  # noqa: RUF012
    #: A list of blocks to add to the right column
    right_column_widgets: list[Block] = []  # noqa: RUF012

    def __init__(
        self,
        left_column_width: int | None = None,
        left_column_widgets: list[Block] | None = None,
        right_column_widgets: list[Block] | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.left_column_width = (
            left_column_width if left_column_width else self.left_column_width
        )
        self.left_column_widgets = (
            left_column_widgets
            if left_column_widgets is not None
            else deepcopy(self.left_column_widgets)
        )
        self.right_column_widgets = (
            right_column_widgets
            if right_column_widgets is not None
            else deepcopy(self.right_column_widgets)
        )
        left_viewport_widths = {"md": str(self.left_column_width)}
        right_viewport_widths = {"md": str(12 - self.left_column_width)}
        self.add_column(
            Column(
                *self.left_column_widgets,
                name="left",
                base_width=12,
                viewport_widths=left_viewport_widths,
            )
        )
        self.add_column(
            Column(
                *self.right_column_widgets,
                name="right",
                base_width=12,
                viewport_widths=right_viewport_widths,
            )
        )
