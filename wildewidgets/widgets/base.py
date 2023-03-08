#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections.abc import Iterable as IterableABC
from copy import deepcopy
from typing import Union, List, Dict, Iterable, Any, Optional
import warnings

from django.template.loader import get_template
from django.templatetags.static import static


class Widget:
    """
    The base class from which all widgets should inherit.
    """
    title: Optional[Union[str, "Widget"]] = None
    icon: str = 'gear'

    def __init__(
        self,
        *args,
        title: Union[str, "Widget"] = None,
        icon: str = None,
        **kwargs
    ):
        self.title = title if title else self.title
        self.icon = icon if icon else self.icon
        super().__init__(*args, **kwargs)

    def get_title(self) -> Union[str, "Widget"]:
        return self.title

    def is_visible(self) -> bool:
        return True

    def get_template_context_data(self, **kwargs) -> Dict[str, Any]:
        return kwargs

    def get_content(self) -> "Widget":
        raise NotImplementedError


class TemplateWidget(Widget):

    #: The name of the template to use to render this widget
    template_name: Optional[str] = None

    def get_content(self, **kwargs) -> str:
        """
        Actually render us to a string.  This is the method that the
        ``wildewidgets`` template tag will call (via
        :py:meth:`wildewidgets.templatetags.wildewidgets.WildewidgetsNode.render`)
        to render the widget into a containing template.

        Returns:
            Our rendered HTML.
        """
        context = self.get_context_data(**kwargs)
        html_template = get_template(self.get_template())
        content = html_template.render(context)
        return content

    def get_template(self) -> str:
        """
        Return the name to the Django template we want to use to render
        this :py:class:`TemplateWidget`.

        Returns:
            The name of the template to use to render us.

        Raises:
            ImproperlyConfigured: no template name was provided.
        """
        return self.template_name

    def get_context_data(self, *args, **kwargs) -> Dict[str, Any]:
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

        >>> block = Block(
            'Hello World',
            tag='a',
            name='foo',
            modifier='bar',
            css_class='blah dah',
            attributes={'href': 'https://example.com'}
        )

        When rendered in the template with the ``wildewdigets`` template tag, this
        will produce::

            <a href="https://example.com" class="foo foo--bar blah dah">Hello World</a>


    Args:
        *blocks: any content to be rendered in the block, including other blocks, or
            plain strings

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
                f'"{name}" must be provided as either a keyword argument or as a class attribute'
            )

    template_name: str = "wildewidgets/block.html"

    #: block is the official wildewidgets name of the block; it can't be changed
    #: by constructor kwargs
    block: str = ''

    #: The name of the HTML element to use as our tag, e.g. ``div``
    tag: str = 'div'
    #: The CSS class that will be added to this element to as an identifier for
    #: this kind of block
    name: Optional[str] = None
    #: If specified, also add a class named ``{name}--{modifier}`` to the CSS
    #: classes
    modifier: Optional[str] = None
    #: A string of CSS classes to apply to this block
    css_class: str = ''
    #: The CSS ``id`` for this block
    css_id: Optional[str] = None
    #: A list of strings or Blocks that will be the content for this block
    contents: List[Union[str, Widget]] = []
    #: Additional HTML attributes to set on this block
    attributes: Dict[str, str] = {}
    #: Additional ``data-bs-`` attributes to set on this block
    data_attributes: Dict[str, str] = {}
    #: Additional ``aria-`` attributes to set on this block
    aria_attributes: Dict[str, str] = {}
    #: If ``True``, this block uses no close tag
    empty: bool = False
    #: The Javascript to apply to this block.  It will appear in the HTML directly after
    #: the block appears.  Do not surround this with a ``<script>`` tag; that will be
    #: done for you.
    script: Optional[str] = None

    def __init__(
        self,
        *blocks,
        tag: str = None,
        name: str = None,
        modifier: str = None,
        css_class: str = None,
        css_id: str = None,
        empty: bool = None,
        script: str = None,
        attributes: Dict[str, str] = None,
        data_attributes: Dict[str, str] = None,
        aria_attributes: Dict[str, str] = None
    ):
        super().__init__()
        self._name = name if name is not None else self.name
        self._modifier = modifier if modifier is not None else self.modifier
        self._css_class = css_class if css_class is not None else self.css_class
        if self._css_class is None:
            # Somebody actually went and set our class attribute to ``None``
            self._css_class = ''
        self._css_id = css_id if css_id is not None else self.css_id
        self._tag = tag if tag is not None else self.tag
        self.contents = blocks if blocks else deepcopy(self.contents)
        self.empty = empty if empty is not None else self.empty
        self.script = script if script is not None else self.script
        self._attributes = attributes if attributes is not None else deepcopy(self.attributes)
        self._data_attributes = data_attributes if data_attributes is not None else deepcopy(self.data_attributes)
        self._aria_attributes = aria_attributes if aria_attributes is not None else deepcopy(self.aria_attributes)
        if self.empty and len(blocks) > 0:
            raise ValueError(
                f"{self.__class__.__name__}: This block takes no content because empty=True."
            )
        if self.empty:
            self.template_name = 'wildewidgets/block--simple.html'
        #: The internal list of blocks that are this block's content
        self.blocks: List[Union[str, Widget]] = []
        self.add_blocks()

    @property
    def css_classes(self) -> List[str]:
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
    def css_classes(self, classes: List[str]) -> None:
        """
        Set our CSS classes to be ``classes``.

        Note:
            Don't try to change :py:attr:`name``, :py:attr:`block`` or
            :py:attr:`modifier`` classes with this; set them by direct assigment
            instead.

        Returns:
            The list of the CSS classes for this block, excluding the
            ``block``, ``name`` and ``modifier`` classes.
        """
        self._css_class = ' '.join(classes)

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
            if ' ' in self._css_class:
                # Ensure we don't try to add ``None`` or empty string here
                classes = self._css_class.split()
            else:
                classes = [self._css_class]
            if css_class not in classes:
                classes.append(css_class)
            self._css_class = ' '.join(list(classes))

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
            self._css_class = ' '.join(list(classes))

    def add_blocks(self) -> None:
        """
        Add each block in :py:attr:`contents` to our :py:attr:`blocks` list.

        Note:
            This is here so it can be overridden.
        """
        for block in self.contents:
            self.add_block(block)

    def add_block(self, block: Union[str, Widget]) -> None:
        """
        Add a block to our content.  This will appear inside the tag for this block.

        Args:
            block: the block to add to our content
        """
        if self.empty:
            raise ValueError(
                f"{self.__class__.__name__}: This block takes no content because empty=True."
            )
        self.blocks.append(block)

    def get_script(self) -> Optional[str]:
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

    def get_context_data(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Update the template context dictionary used when rendering this block.

        Keyword Args:
            **kwargs: the current context dictionary

        Returns:
            The updated context dictionary
        """
        context = super().get_context_data(*args, **kwargs)
        css_class = ' '.join(self.css_classes)
        name = self._name if self._name is not None else ''
        block = self.block if self.block is not None else ''
        if name and self._modifier:
            modifier = f'{name}--{self.modifier}'
        else:
            modifier = ''
        context['tag'] = self._tag
        context['block_name'] = block
        context['name'] = name
        context['css_classes'] = ' '.join([name, modifier, block, css_class]).strip()
        context['script'] = self.get_script()
        context['css_id'] = self._css_id
        context['blocks'] = self.blocks
        context['attributes'] = self._attributes
        context['data_attributes'] = self._data_attributes
        context['aria_attributes'] = self._aria_attributes
        return context


class Container(Block):
    """
    A `Bootstrap container <https://getbootstrap.com/docs/5.2/layout/containers/>`_

    Example::

        >>> c = Container(size='lg')

    Keyword Args:
        size: The max viewport size for the container, in bootstrap sizes, or
            ``fluid``.

    Raises:
        ValueError: ``size`` was not one of the valid sizes
    """
    VALID_SIZES: List[str] = [
        'sm',
        'md',
        'lg',
        'xl',
        'xxl',
        'fluid'
    ]

    #: The max viewport size for the container, in bootstrap sizes, or
    #:``fluid``.
    size: Optional[str] = None

    def __init__(
        self,
        *blocks,
        size: str = None,
        **kwargs
    ):
        self.size = size if size else self.size
        if self.size and self.size not in self.VALID_SIZES:
            raise ValueError(
                f"\"{self.size}\" is not a valid container size.  Valid sizes: {', '.join(self.VALID_SIZES)}")
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
        #     padding: 0;
        # }
        classes = self.css_classes
        klass = 'container'
        if self.size:
            klass += f'-{self.size}'
        classes.insert(0, klass)
        self.css_classes = classes


class Link(Block):
    """
    This is a simple ``<a>`` tag.  We made it into its own block because we need `<a>`
    tags so often.

    Example::

        >>> link = Link('click here', url='https://example.com')

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

    tag: str = 'a'

    #: The contents of the ``<a>``.  This can be string, a :py:class:`Block`,
    #: or an iterable of strings and :py:class:`Block` objects.
    contents: Union[str, Block, Iterable[Union[str, Block]]] = None
    #: The URL of the ``<a>``
    url: str = '#'
    #: The value of the ``role`` attribute for the link
    role: str = 'link'
    #: The value of the ``title`` attribute for the link
    title: Optional[str] = None
    #: The target for this link, aka the context in which the linked resource
    #: will open.
    target: Optional[str] = None

    def __init__(
        self,
        *contents: Union[str, Block],
        url: str = None,
        role: str = None,
        title: str = None,
        target: str = None,
        **kwargs
    ):
        self.url = url if url else self.url
        self.role = role if role else self.role
        self.title = title if title else self.title
        self.target = target if target else self.target
        # FIXME: validate url
        # FIXME: validate that title and role are htmleescaped
        if contents:
            self.contents: Iterable[Union[str, Block]] = contents
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
        self._attributes['href'] = self.url
        self._attributes['role'] = self.role
        if self.title:
            self._attributes['title'] = self.title
        if self.target:
            self._attributes['target'] = self.title


class UnorderedList(Block):
    """
    An HTML unordered list, aka a ``<ul>`` tag.

    This wraps each item in :py:attr:`contents` with ``<li>``.

    Example:

        With constructor arguments::

            >>> items = ['foo', 'bar', 'baz', Link['barney', url='https://example.com]]
            >>> ul = UnorderedList(*items)

        With :py:meth:`add_block`::

            >>> items = ['foo', 'bar', 'baz', Link['barney', url='https://example.com]]
            >>> ul = UnorderedList()
            >>> for item in items:
            ...     ul.add_block(item)

    """

    tag: str = 'ul'

    def add_block(self, block: Union[str, Block], **kwargs) -> None:
        """
        Wrap ``block``  in an ``<li>``
        :py:class:`wildewidgets.widgets.base.Block` append it to
        :py:attr:`blocks`, using ``**kwargs`` as the keyword arguments for ``Block``.

        If ``block`` is already an ``<li>``, just append it to :py:attr:`blocks`.
        """
        if isinstance(block, Block) and block.tag == 'li':
            self.blocks.append(block)

        self.blocks.append(Block(block, tag='li', **kwargs))


class OrderedList(UnorderedList):
    """
    An HTML ordered list, aka a ``<ol>`` tag.

    This wraps each item in :py:attr:`contents` with ``<li>``.

    Example:

        With constructor arguments::

            >>> items = ['foo', 'bar', 'baz', Link['barney', url='https://example.com]]
            >>> ul = OrderedList(*items)

        With :py:meth:`add_block`::

            >>> items = ['foo', 'bar', 'baz', Link['barney', url='https://example.com]]
            >>> ul = OrderedList()
            >>> for item in items:
            ...     ul.add_block(item)
    """
    tag: str = 'ol'


class HTMLList(UnorderedList):
    """
    An unordered HTML list.

    .. deprecated:: 0.14.0

        Use :py:class:`UnorderedList` instead.  Change this::

            >>> items = ['foo', 'bar', 'baz', Link['barney', url='https://example.com]]
            >>> block = HTMLList(items=items)

        To this::

            >>> items = ['foo', 'bar', 'baz', Link['barney', url='https://example.com]]
            >>> block = UnorderedList(*items)

    """
    def __init__(self, *args, items: List[str] = None, **kwargs):
        warnings.warn(
            'Deprecated in 0.14.0.  Use UnorderedList instead', DeprecationWarning, stacklevel=2
        )
        if not items:
            items = []
        super().__init__(*items, **kwargs)


class Image(Block):
    """
    An ``<img>``::

        <img src="image.png" alt="My Image" width="100%">

    Example:

        >>> block = Image(src=static('myapp/images/img.png'), alt='The Image')

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

    tag: str = 'img'
    block: str = 'image'

    #: The URL of the image.  Typically this will be something like :
    #``static('myapp/images/image.png')``.  The default is to use a placeholder
    #: image to remind you that you need to fix this.
    src: Optional[str] = None
    #: the value of the ``width`` attribute for the <img>
    width: Optional[str] = None
    #: the value of the ``height`` attribute for the <img>
    height: Optional[str] = None
    #: The value of the ``alt`` tag for the <img>.  If this is not set either
    #: here or in our contructor kwargs, we'll raise ``ValueError`` (to enforce
    #: ADA)
    alt: Optional[str] = None

    def __init__(
        self,
        src: str = None,
        height: str = None,
        width: str = None,
        alt: str = None,
        **kwargs
    ):
        self.src = src if src else self.src
        if not self.src:
            self.src = static('wildewidgets/images/placeholder.png')
        # FIXME: validate src as a URL/Path
        self.width = width if width else self.width
        self.height = height if height else self.height
        self.alt = alt if alt else self.alt
        super().__init__(**kwargs)
        if self.src:
            self._attributes['src'] = src
        if self.width:
            self._attributes['width'] = width
        if not self.alt:
            raise ValueError('You must provide an "alt" attribute for your Image')
        self._attributes['alt'] = self.alt


class LinkedImage(Link):
    """
    An ``<img>`` wrapped in an ``<a>``::

        <a href="#">
            <img src="image.png" alt="My Image" width="100%">
        </a>

    Note:

        If you want to modify the encapsulated image (to add css classes, for
        example), you can do so by modifying the attributes on :py:attr:`image`
        after constructing the ``LinkedImage``::

            >>> block = LinkedImage(image_src='image.png', image_alt='My Image',
                url='http://example.com')
            >>> block.image.add_class('my-extra-class')
            >>> block.image._css_id = 'the-image'

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

    block: str = 'linked-image'

    #: The URL of the image.  Typically this will be something like
    #: ``static('myapp/images/image.png')``
    image_src: Optional[str] = None
    #: the value of the ``width`` attribute for the ``<img>``.
    image_width: Optional[str] = None
    #: The value of the ``alt`` tag for the ``<img>``.  If this is not set either
    #: here or in our contructor kwargs, we'll raise ``ValueError`` to enforce
    #: WCAG 2.0 compliance.
    image_alt: Optional[str] = None

    def __init__(
        self,
        image_src: str = None,
        image_width: str = None,
        image_alt: str = None,
        **kwargs
    ):
        self.image_src = image_src if image_src else self.image_src
        if not self.image_src:
            self.image_src = static('sphinx_hosting/images/placeholder.png')
        self.image_width = image_width if image_width else self.image_width
        self.image_alt = image_alt if image_alt else self.image_alt
        #: The actual image block that we will wrap with an ``<a>``
        self.image: Image = Image(src=self.image_src, width=self.image_width, alt=self.image_alt)
        super().__init__(self.image, **kwargs)


class WidgetStream(Block):
    template_name: str = 'wildewidgets/widget_stream.html'
    block: str = 'widget-stream'
    widgets: List[Widget] = []

    def __init__(self, widgets: List[Widget] = None, **kwargs):
        self._widgets = widgets if widgets else deepcopy(self.widgets)
        super().__init__(**kwargs)

    @property
    def is_empty(self) -> bool:
        return len(self._widgets) == 0

    def add_widget(self, widget, **kwargs):
        wrapper = Block(widget, **kwargs)
        wrapper.block = f"{self.block}__widget"
        self._widgets.append(wrapper)

    def get_context_data(self, *args, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(*args, **kwargs)
        context['widgets'] = self._widgets
        return context
