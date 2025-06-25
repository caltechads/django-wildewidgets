from __future__ import annotations

from copy import deepcopy
from typing import Any, cast

from django.core.exceptions import ImproperlyConfigured

from .base import Block


class DatagridItem(Block):
    """
    Implements a `Tabler datagrid-item
    <https://preview.tabler.io/docs/datagrid.html>`_ It should be used with
    :py:class:`Datagrid`.

    Note:
        Unlike :py:class:`wildewidgets.widgets.base.Block`,
        :py:class:`DatagridItem` requires either :py:attr:`contents` to be set,
        or the block contents to be provided as positional arguments.

    Examples:
        Create a :py:class:`DatagridItem` with a title and content:

        .. code-block:: python

            from wildewidgets import DatagridItem, Datagrid

            item = DatagridItem(
                "This is the content of the item.",
                title="My Item",
                url="https://example.com"
            )

            grid = Datagrid(item)

            # or

            grid = Datagrid()
            grid.add_item(item)


    Args:
        *blocks: strings or :py:class:`wildewidgets.widgets.base.Block` objects
            to add to our ``datagrid-item``.  If :py:attr:`contents` is not set,
            these blocks will be used as the contents of the ``datagrid-item``.

    Keyword Args:
        title: the ``datagrid-title`` of the ``datagrid-item``
        url: URL to use to turn content into a hyperlink

    Raises:
        ValueError: either the ``title`` was empty, or no contents were provided
        ImproperlyConfigured: :py:attr:`url` was set, and there is more than one block
            in :py:attr:`contents`

    """

    block: str = "datagrid-item"

    #: the ``datagrid-title`` of the ``datagrid-item``
    title: str | None = None
    #: a URL to use to turn our contents into a hyperlink
    url: str | None = None

    def __init__(
        self,
        *blocks: Any,
        title: str | None = None,
        url: str | None = None,
        **kwargs: Any,
    ) -> None:
        self.title = title if title else self.title
        assert self.title is not None, "title is required"  # noqa: S101
        if not self.title:
            msg = (
                '"title" is required as either a keyword argument or as a class '
                "attribute"
            )
            raise ValueError(msg)
        self.url = url if url else self.url
        super().__init__(*blocks, **kwargs)

    def add_blocks(self) -> None:
        """
        Add our content.

        If :py:attr:`url` is set, and there is only one block in
        :py:attr:`contents`, wrap that block in a :py:class:`wildewidgets.Link`.

        Raises:
            ImproperlyConfigured: :py:attr:`url` was set, and there is more than
                one block in :py:attr:`contents`

        """
        if self.url:
            if len(self.contents) == 1:
                wrapper: Block = Block(
                    self.contents[0],
                    tag="a",
                    attributes={"href": self.url},
                    name="datagrid-content",
                )
            else:
                msg = (
                    f"{self.__class__.__name__}: url should only be set if contents "
                    "are a single block"
                )
                raise ImproperlyConfigured(msg)
        elif len(self.contents) == 1:
            if not isinstance(self.contents[0], Block):
                # Wrap the text in a block to allow us to assign the datagrid-content
                # class to it
                wrapper = Block(self.contents[0], name="datagrid-content")
            else:
                wrapper = self.contents[0]
        else:
            wrapper = Block(name="datagrid-content")
            for block in self.contents:
                wrapper.add_block(block)
        self.add_block(Block(self.title, name="datagrid-title"))  # type: ignore[arg-type]
        self.add_block(wrapper)


DatagridItemDef = DatagridItem | tuple[str, str] | tuple[str, str, dict[str, Any]]


class Datagrid(Block):
    """
    Implements a `Tabler Data grid <https://preview.tabler.io/docs/datagrid.html>`_
    It contains :py:class:`DatagridItem` objects.

    Examples:
        Add :py:class:`DatagridItem` objects to this in one of these ways:

        As constructor arguments::

            >>> item1 = DatagridItem(title='foo', content='bar', url="https://example.com")
            >>> item2 = DatagridItem(title='baz', content='barney')
            >>> item3 = ['foo', 'bar']
            >>> grid = Datagrid(item1, item2, item3)

        By using :py:meth:`add_block` with a :py:class:`DatagridItem`:

            >>> grid = Datagrid(item1, item2, item3)
            >>> grid.add_block(DatagridItem(title='foo', content='bar'))

        By using :py:meth:`add_item`::

            >>> grid = Datagrid(item1, item2, item3)
            >>> grid.add_item('foo', 'bar')

    Args:
        *items: a list of ``datagrid-item`` definitions or
        *:py:class:`DatagridItem` objects.

    """

    block: str = "datagrid"
    #: a list of ``datagrid-items`` to add to our content
    items: list[DatagridItemDef] = []  # noqa: RUF012

    def __init__(self, *items: DatagridItemDef, **kwargs: Any) -> None:
        self.items = list(items) if items else deepcopy(self.items)
        super().__init__(**kwargs)
        for item in items:
            if isinstance(item, DatagridItem):
                self.add_block(item)
            elif isinstance(item, tuple):
                if len(item) == 2:  # noqa: PLR2004
                    item = cast("tuple[str, str]", item)
                    self.add_item(item[0], item[1])
                else:
                    item = cast("tuple[str, str, dict[str, Any]]", item)
                    self.add_item(item[0], item[1], **item[2])

    def add_item(
        self,
        title: str,
        content: str | Block | list[str | Block],
        url: str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Add a :py:class:`DatagridItem` to our block contents, with
        ``datagrid-title`` of ``title`` and datagrid.

        Examples:
            Start with our grid::

                >>> dg = DataGrid()

            Add a simple key/value::

                >>> dg.add_item('Version', '1.2.3')

            Add a block as the value, and wrap it in a :py:class:`wildewdigets.Link`::

                >>> dg.add_item(
                    'Gravatar',
                    Image(src=static('myapp/images/gravatar.png'), alt='MyGravatar'),
                    url='https://www.google.com'
                )

            Add a list of blocks as the value::

                >>> dg.add_item(
                    'Contributors',
                    [
                        ImageLink(
                            src=static('myapp/images/fred-gravatar.png',
                            alt='Fred'
                            url='https://www.fred.com'
                        ),
                        ImageLink(
                            src=static('myapp/images/barney-gravatar.png',
                            alt='Barney'
                            url='https://www.barney.com'
                        )
                    ],
                    css_class='d-flex flex-row'
                )


        Note:
            To add a :py:class:`DatagridItem` directly, use :py:meth:`add_block`.

        Keyword Args:
            title: the ``datagrid-title`` of the ``datagrid-item``
            content: the ``datagrid-content`` of the ``datagrid-item``
            url: URL to use to turn content into a hyperlink
            **kwargs: additional keyword arguments passed to the
                :py:class:`DatagridItem` constructor

        """
        if isinstance(content, (str, Block)):
            content = [content]
        self.add_block(DatagridItem(*content, title=title, url=url, **kwargs))
