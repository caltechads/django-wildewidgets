from __future__ import annotations

import warnings
from collections.abc import Iterable
from collections.abc import Iterable as IterableABC
from copy import deepcopy
from typing import Any, ClassVar, Final, Literal, TypeVar

from django.template.loader import get_template
from django.templatetags.static import static

# Define a type variable for Widget return types
WidgetT = TypeVar("WidgetT", bound="Widget")


class Widget:
    """
    The base class from which all widgets should inherit.

    This class provides the foundation for all wildewidgets components. It defines
    the basic interface that all widgets must implement and provides common
    functionality.

    Attributes:
        title: An optional title for the widget that can be displayed in UI elements.
        icon: A default icon identifier used for rendering widget-related icons.

    """

    title: str | Widget | None = None
    icon: str = "gear"

    def __init__(
        self,
        *args: Any,
        title: str | Widget | None = None,
        icon: str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize a new Widget instance.

        Args:
            *args: Variable length argument list passed to parent.

        Keyword Args:
            title: Optional title to display with the widget.
            icon: Optional icon identifier to use for this widget.
            **kwargs: Arbitrary keyword arguments passed to parent.

        """
        self.title = title if title else self.title
        self.icon = icon if icon else self.icon
        super().__init__(*args, **kwargs)

    def get_title(self) -> str | Widget | None:
        """
        Retrieve the widget's title.

        Returns:
            The widget's title string, widget object, or None if no title is set.

        """
        return self.title

    def is_visible(self) -> bool:
        """
        Determine if this widget should be visible.

        Can be overridden by subclasses to conditionally show/hide widgets.

        Returns:
            Boolean indicating whether this widget should be visible. Default is True.

        """
        return True

    def get_template_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Get the base context data for rendering the widget.

        Args:
            **kwargs: Context data to include.

        Returns:
            Dictionary of context data for template rendering.

        """
        return kwargs

    def get_content(self) -> Any:
        """
        Get the rendered content of this widget.

        This method must be implemented by subclasses to produce the actual
        rendered content of the widget.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.

        Returns:
            The rendered content (typically HTML).

        """
        raise NotImplementedError


class TemplateWidget(Widget):
    """
    A widget that renders content using a Django template.

    This class extends :py:class:`Widget` to provide template-based rendering
    capabilities.  Subclasses should define a :py:attr:`template_name` that
    points to a valid Django template.

    Attributes:
        template_name: Path to the Django template to use for rendering.

    """

    template_name: str | None = None

    def get_content(self, **kwargs: Any) -> str:
        """
        Render the widget using its template.

        This method retrieves the appropriate template, populates the context
        with data from get_context_data(), and renders the template to a string.

        Args:
            **kwargs: Additional context data to include in the template.

        Returns:
            String containing the rendered HTML content.

        """
        context = self.get_context_data(**kwargs)
        html_template = get_template(self.get_template())
        return html_template.render(context)

    def get_template(self) -> str:
        """
        Return the name to the Django template we want to use to render
        this :py:class:`TemplateWidget`.

        Returns:
            The name of the template to use to render us.

        Raises:
            ImproperlyConfigured: no template name was provided.

        """
        if not self.template_name:
            msg = f"No template found for {self.__class__.__name__})"
            raise ValueError(msg)
        return self.template_name

    def get_context_data(self, *_: Any, **kwargs: Any) -> dict[str, Any]:
        return kwargs

    def __str__(self) -> str:
        return self.get_content()


class Block(TemplateWidget):
    """
    Render a single HTML element.

    All the constructor parameters can be set in a subclass of this class as
    class attributes.  Parameters to the constructor override any defined class
    attributes.

    Example:

        .. code-block:: python

            from wildewidgets import Block

            block = Block(
                'Hello World',
                tag='a',
                name='foo',
                modifier='bar',
                css_class='blah dah',
                attributes={'href': 'https://example.com'}
            )

        When rendered in the template with the ``wildewidgets`` template tag, this
        will produce:

        .. code-block:: html

            <a href="https://example.com" class="foo foo--bar blah dah">Hello World</a>


    Args:
        *blocks: any content to be rendered in the block, either other blocks, or
            plain strings, or a mix of both.  If this is not specified, the
            :py:attr:`contents` attribute will be used instead.  If you specify
            this, it will override :py:attr:`contents`.

    Keyword Args:
        tag: the name of the HTML element to use as our tag, e.g. ``div``
        name: This CSS class will be added to the classes to identify this
            block
        modifier: If specified, also add a class named ``{name}--{modifier}`` to the
            CSS classes
        css_class: a string of CSS classes to apply to the block
        css_id: Use this as the ``id`` attribute for the block
        attributes: Set any additional attributes for the block
        data_attributes: Set ``data-bs-`` attributes for the block
        aria_attributes: Set ``aria-`` attributes for the block
        empty: if ``True``, this element uses no close tag
        script: Javascript to attach to this block

    Raises:
        ValueError: empty is ``True``, but contents were added to this block

    """

    class RequiredAttrOrKwarg(ValueError):
        def __init__(self, name: str):
            super().__init__(
                f'"{name}" must be provided as either'
                "a keyword argument or as a class attribute"
            )

    #: The name of the template to use to render this block
    template_name: str = "wildewidgets/block.html"

    #: block is the official wildewidgets name of the block; it can't be changed
    #: by constructor kwargs
    block: str = ""

    #: The name of the HTML element to use as our tag, e.g. ``div``
    tag: str = "div"
    #: The CSS class that will be added to this element to as an identifier for
    #: this kind of block
    name: str | None = None
    #: If specified, also add a class named ``{name}--{modifier}`` to the CSS
    #: classes
    modifier: str | None = None
    #: A string of CSS classes to apply to this block
    css_class: str = ""
    #: The CSS ``id`` for this block
    css_id: str | None = None
    #: A list of strings or Blocks that will be the content for this block
    contents: list[str | Widget] = []  # noqa: RUF012
    #: Additional HTML attributes to set on this block
    attributes: ClassVar[dict[str, str]] = {}
    #: Additional ``data-bs-`` attributes to set on this block
    data_attributes: ClassVar[dict[str, str]] = {}
    #: Additional ``aria-`` attributes to set on this block
    aria_attributes: ClassVar[dict[str, str]] = {}
    #: If ``True``, this block uses no close tag
    empty: bool = False
    #: The Javascript to apply to this block.  It will appear in the HTML directly after
    #: the block appears.  Do not surround this with a ``<script>`` tag; that will be
    #: done for you.
    script: str | None = None

    def __init__(
        self,
        *blocks: str | Widget | Block,
        tag: str | None = None,
        name: str | None = None,
        modifier: str | None = None,
        css_class: str | None = None,
        css_id: str | None = None,
        empty: bool | None = None,
        script: str | None = None,
        attributes: dict[str, str] | None = None,
        data_attributes: dict[str, str] | None = None,
        aria_attributes: dict[str, str] | None = None,
    ) -> None:
        super().__init__()
        self._name = name if name is not None else self.name
        self._modifier = modifier if modifier is not None else self.modifier
        self._css_class = css_class if css_class is not None else self.css_class
        if self._css_class is None:
            # Somebody actually went and set our class attribute to ``None``
            self._css_class = ""
        self._css_id = css_id if css_id is not None else self.css_id
        self._tag = tag if tag is not None else self.tag
        self.contents = list(blocks) if blocks else deepcopy(self.contents)
        self.empty = empty if empty is not None else self.empty
        self.script = script if script is not None else self.script
        self._attributes = (
            attributes if attributes is not None else deepcopy(self.attributes)
        )
        self._data_attributes = (
            data_attributes
            if data_attributes is not None
            else deepcopy(self.data_attributes)
        )
        self._aria_attributes = (
            aria_attributes
            if aria_attributes is not None
            else deepcopy(self.aria_attributes)
        )
        if self.empty and len(blocks) > 0:
            msg = (
                f"{self.__class__.__name__}: This block takes no content "
                "because empty=True."
            )
            raise ValueError(msg)
        if self.empty:
            self.template_name = "wildewidgets/block--simple.html"
        #: The internal list of blocks that are this block's content
        self.blocks: list[str | Widget] = []
        self.add_blocks()

    @property
    def css_classes(self) -> list[str]:
        """
        Return a list of our CSS classes.

        Note:
            This excludes the set :py:attr:`name`, :py:attr:`block` and
            :py:attr:`modifier` classes.  Read those directly from their
            attributes instead.

        Returns:
            The list of the CSS classes for this block, excluding the
            ``block``, ``name`` and ``modifier`` classes.

        """
        return list(self._css_class.split())

    @css_classes.setter
    def css_classes(self, classes: list[str]) -> None:
        """
        Set our CSS classes to be ``classes``.

        Note:
            Don't try to change :py:attr:`name``, :py:attr:`block`` or
            :py:attr:`modifier`` classes with this; set them by direct assigment
            instead.

        Args:
            classes: A list of CSS classes to set as our :py:attr:`_css_class`
            attribute.  This will replace any existing classes.

        """
        self._css_class = " ".join(classes)

    def add_class(self, css_class: str) -> None:
        """
        Add a CSS class to our :py:attr:`_css_class` attribute.  This is a
        convenience method to allow us to add a class withouth having to do
        string manipulation.

        Note:
            If you need to change :py:attr:`name` or :py:attr:`modifier`, set them
            directly instead of using this.

        Args:
            css_class: The CSS to add

        """
        # Note: we're purposely not using set() here because Tabler sometimes
        # requires a specific class ordering in order to work properly. set()
        # destroys our ordering.
        if css_class:
            if " " in self._css_class:
                # Ensure we don't try to add ``None`` or empty string here
                classes = self._css_class.split()
            else:
                classes = [self._css_class]
            if css_class not in classes:
                classes.append(css_class)
            self._css_class = " ".join(list(classes))

    def remove_class(self, css_class: str) -> None:
        """
        Remove a CSS class from our :py:attr:`_css_class` attribute.  This is a
        convenience method to allow us to remove a class withouth having to do
        string manipulation.

        Note:
            This method can only remove things from :py:attr:`_css_class`.  You
            can't remove :py:attr:`name`, :py:attr:`modifier` or :py:attr:`block`
            with this method, since those are supposed to be purely informational.

        Args:
            css_class: The CSS to remove

        """
        # Note: we're purposely not using set() here because Tabler sometimes
        # requires a specific class ordering in order to work properly. set()
        # destroys our ordering.
        if css_class:
            # Ensure we don't try to remove ``None`` or empty string here
            classes = self._css_class.split()
            if css_class in classes:
                classes.remove(css_class)
            self._css_class = " ".join(list(classes))

    def add_blocks(self) -> None:
        """
        Add each block in :py:attr:`contents` to our :py:attr:`blocks` list.

        Note:
            This is here so it can be overridden.

        """
        for block in self.contents:
            self.add_block(block)

    def add_block(self, block: str | Widget | Block) -> None:
        """
        Add a block to our content.  This will appear inside the tag for this block.

        Args:
            block: the block to add to our content

        """
        if self.empty:
            msg = (
                f"{self.__class__.__name__}: This block takes no content because "
                "empty=True."
            )
            raise ValueError(msg)
        self.blocks.append(block)

    def get_script(self) -> str | None:
        """
        Return any javascript to attach to this block.

        Note:
            The Javascript will will appear in the HTML directly after the block
            appears.  Do not surround this with a ``<script>`` tag; that will be
            done for you.

        Returns:
            The fully rendered Javascript for this block, if any.

        """
        return self.script

    def get_context_data(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """
        Update the template context dictionary used when rendering this block.

        Args:
            *args: positional arguments (ignored)

        Keyword Args:
            **kwargs: the current context dictionary

        Returns:
            The updated context dictionary

        """
        context = super().get_context_data(*args, **kwargs)
        css_class = " ".join(self.css_classes)
        name = self._name if self._name is not None else ""
        block = self.block if self.block is not None else ""
        modifier = f"{name}--{self._modifier}" if name and self._modifier else ""
        context["tag"] = self._tag
        context["block_name"] = block
        context["name"] = name
        context["css_classes"] = f"{name} {modifier} {block} {css_class}".strip()
        context["script"] = self.get_script()
        context["css_id"] = self._css_id
        context["blocks"] = self.blocks
        context["attributes"] = self._attributes
        context["data_attributes"] = self._data_attributes
        context["aria_attributes"] = self._aria_attributes
        return context


class Container(Block):
    """
    A `Bootstrap container <https://getbootstrap.com/docs/5.2/layout/containers/>`_

    Example:
        .. code-block:: python

            from wildewidgets import Container

            c = Container(size='lg')

    Keyword Args:
        size: The max viewport size for the container, in bootstrap sizes, or
            ``fluid``.

    Raises:
        ValueError: ``size`` was not one of the valid sizes

    """

    #: The valid sizes for the Tabler container.  These are the bootstrap sizes
    #: ``sm``, ``md``, ``lg``, ``xl``, ``xxl`` and ``fluid``.
    VALID_SIZES: Final[list[Literal["sm", "md", "lg", "xl", "xxl", "fluid"]]] = [
        "sm",
        "md",
        "lg",
        "xl",
        "xxl",
        "fluid",
    ]

    #: The max viewport size for the container, in bootstrap sizes, or
    #:``fluid``.
    size: str | None = None

    def __init__(
        self, *blocks: str | Widget, size: str | None = None, **kwargs: Any
    ) -> None:
        self.size = size if size else self.size
        if self.size and self.size not in self.VALID_SIZES:
            valid_sizes = ", ".join(self.VALID_SIZES)
            msg = (
                f'"{self.size}" is not a valid container size.  Valid sizes: "'
                f'{valid_sizes}"'
            )
            raise ValueError(msg)
        super().__init__(*blocks, **kwargs)
        # IMPORTANT: the Tabler rules sometimes expect that the container-* class to
        # be the first class in the class list.  If it is not first, the CSS rules
        # change.  E.g.:
        #
        # .navbar-vertical.navbar-expand-lg > [class^="container"] {
        #     flex-direction: column;
        #     align-items: stretch;
        #     min-height: 100%;
        #     justify-content: flex-start;
        #     padding: 0;}
        classes = self.css_classes
        klass = "container"
        if self.size:
            klass += f"-{self.size}"
        classes.insert(0, klass)
        self.css_classes = classes


class Link(Block):
    """
    A simple ``<a>`` tag.  We made it into its own block because we need `<a>`
    tags so often.

    Example:
        .. code-block:: python

            from wildewidgets import Link

            link = Link('click here', url='https://example.com')

    Keyword Args:
        contents: The contents of the ``<a>``.  This can be string, a
            :py:class:`Block`, or an iterable of strings and :py:class:`Block`
            objects.
        url: The URL of the ``<a>``
        title: The value of the ``title`` tag for the link
        role: The value of the ``role`` attribute for the link
        target: The target for this link, aka the context in which the linked
            resource will open.

    """

    #: The name of the HTML element to use as our tag, e.g. ``a``
    tag: str = "a"

    #: The contents of the ``<a>``.  This can be string, a :py:class:`Block`,
    #: or an iterable of strings and :py:class:`Block` objects.
    contents: str | Block | Iterable[str | Block] | None = None  # type: ignore[assignment]
    #: The URL of the ``<a>``
    url: str = "#"
    #: The value of the ``role`` attribute for the link
    role: str = "link"
    #: The value of the ``title`` attribute for the link
    title: str | None = None
    #: The target for this link, aka the context in which the linked resource
    #: will open.
    target: str | None = None

    def __init__(
        self,
        *contents: str | Block,
        url: str | None = None,
        role: str | None = None,
        title: str | None = None,
        target: str | None = None,
        **kwargs: Any,
    ) -> None:
        self.url = url if url else self.url
        self.role = role if role else self.role
        self.title = title if title else self.title
        self.target = target if target else self.target
        # TODO: validate url
        # TODO: validate that title and role are htmleescaped
        if contents:
            self.contents = contents
        else:
            c = self.contents
            if isinstance(c, str):
                self.contents = [c]
            elif isinstance(c, Block):
                self.contents = [deepcopy(c)]
            elif isinstance(c, IterableABC):
                self.contents = deepcopy(c)
            else:
                self.contents = []
        super().__init__(*self.contents, **kwargs)
        self._attributes["href"] = self.url
        self._attributes["role"] = self.role
        if self.title:
            self._attributes["title"] = self.title
        if self.target:
            self._attributes["target"] = self.target


class UnorderedList(Block):
    """
    An HTML unordered list, aka a ``<ul>`` tag.

    This wraps each item in :py:attr:`contents` with ``<li>``.

    Example:
        With constructor arguments:

        .. code-block:: python

            from wildewidgets import UnorderedList, Link

            items = ['foo', 'bar', 'baz', Link['barney', url='https://example.com]]
            ul = UnorderedList(*items)

        With :py:meth:`add_block`:

        .. code-block:: python

            from wildewidgets import UnorderedList, Link

            items = ['foo', 'bar', 'baz', Link['barney', url='https://example.com]]
            ul = UnorderedList()
            for item in items:
                ul.add_block(item)

    """

    #: The name of the HTML element to use as our tag, e.g. ``ul``
    tag: str = "ul"

    def add_block(self, block: str | Block, **kwargs: Any) -> None:  # type: ignore[override]
        """
        Wrap ``block``  in an ``<li>``
        :py:class:`~wildewidgets.widgets.base.Block` append it to
        :py:attr:`blocks`, using ``**kwargs`` as the keyword arguments for ``Block``.

        If ``block`` is already an ``<li>``, just append it to :py:attr:`blocks`.
        """
        if isinstance(block, Block) and block._tag == "li":
            self.blocks.append(block)
        else:
            self.blocks.append(Block(block, tag="li", **kwargs))


class OrderedList(UnorderedList):
    """
    An HTML ordered list, aka a ``<ol>`` tag.

    This wraps each item in :py:attr:`contents` with ``<li>``.

    Example:
        With constructor arguments:

        ... code-block:: python

            from wildewidgets import OrderedList, Link

            items = ['foo', 'bar', 'baz', Link['barney', url='https://example.com]]
            ul = OrderedList(*items)

        With :py:meth:`add_block`:

        .. code-block:: python

            from wildewidgets import OrderedList, Link

            items = ['foo', 'bar', 'baz', Link['barney', url='https://example.com]]
            ul = OrderedList()
            for item in items:
                ul.add_block(item)

    """

    #: The name of the HTML element to use as our tag, e.g. ``ol``
    tag: str = "ol"


class HTMLList(UnorderedList):
    """
    An unordered HTML list.

    .. deprecated:: 0.14.0

        Use :py:class:`UnorderedList` instead.  Change this:

        .. code-block:: python

            from wildewidgets import HTMLList, Link

            items = ['foo', 'bar', 'baz', Link['barney', url='https://example.com]]
            block = HTMLList(items=items)

        To this:

        .. code-block:: python

            from wildewidgets import UnorderedList, Link

            items = ['foo', 'bar', 'baz', Link['barney', url='https://example.com]]
            block = UnorderedList(*items)

    """

    def __init__(
        self,
        *args: Any,  # noqa: ARG002
        items: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        warnings.warn(
            "Deprecated in 0.14.0.  Use UnorderedList instead",
            DeprecationWarning,
            stacklevel=2,
        )
        if not items:
            items = []
        super().__init__(*items, **kwargs)


class Image(Block):
    """
    An ``<img>``::

        <img src="image.png" alt="My Image" width="100%">

    Example:

        .. code-block:: python

            from wildewidgets import Image
            from django.templatetags.static import static

            block = Image(src=static('myapp/images/img.png'), alt='The Image')

    Keyword Args:
        src: the URL of the image.  Typically this will be something like
            ``static('myapp/images/image.png')`` The default is to use a
            placeholder image to remind you that you need to fix this.
        height: the value of the ``height`` attribute for the ``<img>``
        width: the value of the ``width`` attribute for the ``<img>``
        alt: the value of the ``alt`` tag for the ``<img>``. If this is not
            set either here or as a class attribute, we'll raise ``ValueError`` to
            enforce WCAG 2.0 compliance.

    Raises:
        ValueError: no ``alt`` was provided

    """

    #: The name of the HTML element to use as our tag, e.g. ``img``
    tag: str = "img"
    #: The CSS block name for this widget.  This is used to identify the
    #: widget in the template and to apply CSS styles.
    block: str = "image"

    #: The URL of the image.  Typically this will be something like :
    # ``static('myapp/images/image.png')``.  The default is to use a placeholder
    #: image to remind you that you need to fix this.
    src: str | None = None
    #: the value of the ``width`` attribute for the <img>
    width: str | None = None
    #: the value of the ``height`` attribute for the <img>
    height: str | None = None
    #: The value of the ``alt`` tag for the <img>.  If this is not set either
    #: here or in our contructor kwargs, we'll raise ``ValueError`` (to enforce
    #: ADA)
    alt: str | None = None

    def __init__(
        self,
        src: str | None = None,
        height: str | None = None,
        width: str | None = None,
        alt: str | None = None,
        **kwargs: Any,
    ) -> None:
        self.src = src if src else self.src
        if not self.src:
            self.src = static("wildewidgets/images/placeholder.png")
        # TODO: validate src as a URL/Path
        self.width = width if width else self.width
        self.height = height if height else self.height
        self.alt = alt if alt else self.alt
        super().__init__(**kwargs)
        if self.src:
            self._attributes["src"] = self.src
        if self.width:
            self._attributes["width"] = self.width
        if not self.alt:
            msg = 'You must provide an "alt" attribute for your Image'
            raise ValueError(msg)
        self._attributes["alt"] = self.alt


class LinkedImage(Link):
    """
    An ``<img>`` wrapped in an ``<a>``::

        <a href="#">
            <img src="image.png" alt="My Image" width="100%">
        </a>

    Note:
        If you want to modify the encapsulated image (to add css classes, for
        example), you can do so by modifying the attributes on :py:attr:`image`
        after constructing the ``LinkedImage``:

        .. code-block:: python

            from wildewidgets import LinkedImage
            from django.templatetags.static import static

            block = LinkedImage(
                image_src='image.png',
                image_alt='My Image',
                url='http://example.com'
            )
            block.image.add_class('my-extra-class')
            block.image._css_id = 'the-image'

    Keyword Args:
        image_src: the URL of the image.  Typically this will be something like
            ``static('myapp/images/image.png')``
        image_width: the value of the ``width`` attribute for the ``<img>``
        image_alt: the value of the ``alt`` tag for the ``<img>``. If this is not
            set either here or as a class attribute, we'll raise ``ValueError`` to
            enforce WCAG 2.0 compliance.

    Raises:
        ValueError: no ``alt`` was provided

    """

    block: str = "linked-image"

    #: The URL of the image.  Typically this will be something like
    #: ``static('myapp/images/image.png')``
    image_src: str | None = None
    #: the value of the ``width`` attribute for the ``<img>``.
    image_width: str | None = None
    #: The value of the ``alt`` tag for the ``<img>``.  If this is not set either
    #: here or in our contructor kwargs, we'll raise ``ValueError`` to enforce
    #: WCAG 2.0 compliance.
    image_alt: str | None = None

    def __init__(
        self,
        image_src: str | None = None,
        image_width: str | None = None,
        image_alt: str | None = None,
        **kwargs: Any,
    ) -> None:
        self.image_src = image_src if image_src else self.image_src
        if not self.image_src:
            self.image_src = static("sphinx_hosting/images/placeholder.png")
        self.image_width = image_width if image_width else self.image_width
        self.image_alt = image_alt if image_alt else self.image_alt
        #: The actual image block that we will wrap with an ``<a>``
        self.image: Image = Image(
            src=self.image_src, width=self.image_width, alt=self.image_alt
        )
        super().__init__(self.image, **kwargs)


class WidgetStream(Block):
    """
    A widget that renders a stream of other widgets in sequence.

    This widget allows you to place multiple widgets in a container and render them
    sequentially. It's useful for creating widget dashboards or collections where
    multiple components need to be displayed in order.

    Example:
        .. code-block:: python

            from wildewidgets import WidgetStream, Link, Image

            stream = WidgetStream(
                widgets=[
                    Link('Click here', url='https://example.com'),
                    Image(src='https://example.com/image.png', alt='An image')
                ]
            )

    Note:
        The widgets in the stream are wrapped in a :py:class:`Block` with the
        appropriate CSS class before being added to the stream. This allows for
        consistent styling and layout.

    """

    #: The name of the template to use to render this widget stream
    template_name: str = "wildewidgets/widget_stream.html"
    #: The CSS block name for this widget stream
    block: str = "widget-stream"
    #: Default list of widgets to include in the stream
    widgets: list[Widget] = []  # noqa: RUF012

    def __init__(self, widgets: list[Widget] | None = None, **kwargs: Any) -> None:
        """
        Initialize a widget stream with an optional list of widgets.

        Args:
            widgets: List of widgets to include in the stream. If None, uses the class's
                    default widgets list.
            **kwargs: Additional keyword arguments passed to parent class

        """
        self._widgets = widgets if widgets else deepcopy(self.widgets)
        super().__init__(**kwargs)

    @property
    def is_empty(self) -> bool:
        """
        Check if the widget stream contains any widgets.

        Returns:
            True if the widget stream is empty, False otherwise

        """
        return len(self._widgets) == 0

    def add_widget(self, widget: Widget, **kwargs: Any) -> None:
        """
        Add a widget to the stream.

        The widget is wrapped in a Block with the appropriate CSS class before
        being added to the stream.

        Args:
            widget: The widget to add to the stream
            **kwargs: Additional keyword arguments to pass to the Block constructor

        """
        wrapper = Block(widget, **kwargs)
        wrapper.block = f"{self.block}__widget"
        self._widgets.append(wrapper)

    def get_context_data(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """
        Get the context data for rendering the template.

        Adds the widgets list to the context data.

        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments

        Returns:
            Dictionary containing the context data for template rendering

        """
        context = super().get_context_data(*args, **kwargs)
        context["widgets"] = self._widgets
        return context
