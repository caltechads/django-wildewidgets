from copy import deepcopy
from dataclasses import dataclass, field
import re
from typing import Any, Dict, Iterable, List, Optional, Type, Union, cast

from django.core.exceptions import ImproperlyConfigured

from .base import Block, Container, Link, OrderedList
from .structure import CollapseWidget
from .icons import TablerMenuIcon


path_validator_re = re.compile(
    r'^/\S+$', re.IGNORECASE)


url_validator_re = re.compile(
    r'^(?:http)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)


# ==============================
# Functions
# ==============================

def is_url(text: str) -> bool:
    """
    if ``text`` looks like a URL or path, return ``True``.

    Args:
        text: the string to check

    Returns:
        ``True`` if ``text`` looks like a URL or path, ``False`` otherwise.
    """
    return bool(path_validator_re.search(text) or url_validator_re.search(text))


# ==============================
# Dataclasses
# ==============================

@dataclass
class MenuItem:
    """
    A menu item definition for a :py:class:`Menu`.  :py:attr:`title` is
    required, but the other attributes are not.

    Note:
        We're defining this dataclass so that you don't need to build out the
        entire menu system with the appropriate blocks yourself, but instead can
        nest :py:class:`MenuItem` objects and have us do it for you.

    If no :py:attr:`url` is provided, we will consider this item to be a section
    title in the :py:class:`Menu`.
    """

    #: The text for the item.  If ``url`` is not defined, this will define
    #: a heading within the menu
    text: str
    #: this is either the name of a bootstrap icon, or a :py:class:`Block`
    icon: Optional[Union[str, Block]] = None
    #: The URL for the item.  For Django urls, you will typically do something like
    #: ``reverse('myapp:view')`` or ``reverse_lazy('myapp:view')``
    url: Optional[str] = None
    #: a submenu under this menu item
    items: List["MenuItem"] = field(default_factory=list)
    #: Is this the page we're currently on?
    active: bool = False

    @property
    def is_active(self) -> bool:
        """
        Return ``True`` if we or any item in :py:attr:`items` have :py:attr:`active` equal
        to ``True``.

        Returns:
            Whether this item is active.
        """
        status = self.active
        if not status:
            return any(item.is_active for item in self.items)
        return status

    def set_active(self, text: str) -> bool:
        """
        If ``text`` looks like a URL or path, look at our :py:attr:`url` and set
        :py:attr:`active` to ``True`` if they are equal.

        If ``text`` does not look like a URL or path, look at our :py:attr:`text` and set :py:attr:`active` to ``True``.

        If we find no match, set :py:attr:`active` to `False`, and try doing
        :py:meth:`set_active` on our :py:attr:`items`. Stop looking when we find
        the first item that matches ``text``.

        Args:
            text: the value to which to compare our :py:attr:`text`

        Returns:
            If we actually did set someone's :py:attr:`active` to ``True``, return
            ``True``, otherwise return False
        """
        if is_url(text):
            target = self.url
        else:
            target = self.text
        if target == text:
            self.active = True
            return True
        self.active = False
        for item in self.items:
            if item.set_active(text):
                return True
        return False


@dataclass
class BreadcrumbItem:
    """
    A dataclass that is used to register crumbs with :py:class:`BreadcrumbBlock`.
    """
    #: The title for the breadcrumb
    title: str
    #: The optional URL for the breadcrumb
    url: str = None


# ==============================
# Blocks
# ==============================

class BreadcrumbBlock(Block):
    """
    A block that renders a `Bootstrap Breadcrumb
    <https://getbootstrap.com/docs/5.2/components/breadcrumb/>`_ component.

    Typically how you will use this is to define a base set of breadcrumbs
    (which typically just has your home page in it), and then add additional
    breadcrumbs in your views.

    Example::

        from django.views import View
        from wildewdigets import BreadcrumbItem, BreadcrumbBlock

        class BaseBreadCrumbs(BreadcrumbBlock):

            def __init__(self, *args, **kwargs):
                self.add_breadcrumb('Home', url='/home')

        class MyView(View):

            def get_context_data(self, **kwargs):
                kwargs = super().get_context_data(**kwargs)
                breadcrumbs = BaseBreadCrumbs()
                breadcrumbs.add_breadcrumb('MyView')
                kwargs['breadcrumbs'] = breadcrumbs
                return kwargs

    Keyword Args:
        title_class: Apply this string of CSS classes to each breadcrumb title
    """

    tag: str = 'nav'
    aria_attributes: Dict[str, str] = {'label': 'breadcrumb'}

    #: Apply this string of CSS classes to each breadcrumb title
    title_class: Optional[str] = None
    #: The base set of breadcrumb items
    items: List[BreadcrumbItem] = []

    def __init__(self, *args, title_class: str = None, **kwargs):
        self.title_class = title_class if title_class else self.title_class
        super().__init__(*args, **kwargs)
        #: The list of :py:class:`BreadcrumbItem` objects from which we will
        #: build our breadcrumb HTML
        self.items = deepcopy(self.items)
        #: The ``<ol>`` that holds our breadcrumbs
        self.breadcrumbs = OrderedList(name='breadcrumb')
        self.add_block(self.breadcrumbs)

    def add_breadcrumb(self, title: str, url: str = None) -> None:
        """
        Add a new breadcrumb item to this :py:class:`BreadcrumbBlock`.

        Example:

            >>> breadcrumbs = BreadcrumbBlock()
            >>> breadcrumbs.add_breadcrumb('Home', url='/home'))
            >>> breadcrumbs.add_breadcrumb('Project')

            This will produce this HTML::

                <nav aria-label="breadcrumb">
                  <ol class="breadcrumb">
                    <li class="breadcrumb-item"><a href="/home">Home</a></li>
                    <li class="breadcrumb-item active">Project</li>
                  </ol>
                </nav>

        Args:
            title: the text for the breadcrumb item

        Keyword Args:
            url: the url for the breadcrumb item

        """
        self.items.append(BreadcrumbItem(title=title, url=url))

    def get_context_data(self, *args, **kwargs) -> Dict[str, Any]:
        for item in self.items:
            if self.title_class:
                title = Block(item.title, tag='span', css_class=self.title_class)
            else:
                title = item.title
            if item.url:
                block = Link(title, url=item.url)
            else:
                block = title
            self.breadcrumbs.add_block(block, name='breadcrumb-item')
        # Make the last li be active
        self.breadcrumbs.blocks[-1].add_class('active')
        return super().get_context_data(*args, **kwargs)

    def flatten(self) -> str:
        """
        Return a string of the titles of all the breadcrumbs.
        """
        return ' - '.join([item.title for item in self.items])


class NavigationTogglerButton(Block):
    """
    The ``navbar-toggler`` button for hiding and showing menus in responsive
    `Bootstrap Navbar containers
    <https://getbootstrap.com/docs/5.2/components/navbar/#responsive-behaviors>`_
    ,  styled with some Tabler styling. This is the hamburger icon that causes
    the menus to appear and disappear when we drop below a specific viewport
    size.

    Example::

        >>> toggler = NavigationTogglerButton(target='the_target')

    Keyword Args:
        target: the CSS id of the tag to toggle
        label: the ARIA label of this button
    """

    tag: str = 'button'
    block: str = 'navbar-toggler'
    css_class: str = 'collapsed'
    attributes: Dict[str, str] = {'type': 'button'}
    data_attributes: Dict[str, str] = {'toggle': 'collapse'}
    aria_attributes: Dict[str, str] = {'expanded': 'false'}

    #: The CSS id of the tag that this button toggles
    target: Optional[str] = None
    #: The ARIA label for this button
    label: str = 'Toggle navigation'

    def __init__(self, target: str = None, label: str = None, **kwargs):
        self.target = target if target else self.target
        self.label = label if label else self.label
        if not self.target:
            raise ValueError(
                'No target supplied; define it either as a constructor kwarg or as a class attribute'
            )
        super().__init__(**kwargs)
        self._aria_attributes['label'] = self.label
        self._aria_attributes['controls'] = self.target
        self._data_attributes['target'] = f"#{self.target.lstrip('#')}"
        self.add_block(
            Block(tag='span', name='navbar-toggler-icon')
        )


class Navbar(Block):
    """
    A horizontal `Bootstrap Navbar <https://getbootstrap.com/docs/5.2/components/navbar>`_.

    Examples:

        With a subclass::

            class MyMenu(Menu):
                items = [MenuItem(text='One', url='/one', icon='target)]

            class MyNavbar(Navbar):
                branding = LinkedImage(src='/static/branding.png', alt='My Brand', url='#')
                contents = [MyMenu()]

        With :py:class:`Navbar` constructor arguments::

            >>> branding = LinkedImage(src='/static/branding.png', alt='My Brand', url='#')
            >>> items = [MenuItem(text='One', url='/one'), ... ]
            >>> menu = Menu(*items)
            >>> sidebar = Navbar(menu, branding=branding)

        Adding menus later::

            >>> items2 = [MenuItem(text='Foo', url='/foo'), ... ]
            >>> menu2 = Menu(*items)
            >>> sidebar.add_to_menu_section(menu2)

    Note:

        You can add other things to the menu section than just menus.  For instance,
        a search form::

            class SearchFormBlock(Block):
                ...

            class MyMenu(Menu):
                items = [MenuItem(text='One', url='/one', icon='target)]

            class MyNavbar(Navbar):
                branding = LinkedImage(src='/static/branding.png', alt='My Brand', url='#')
                contents = [SearchFormBlock(), MyMenu()]

    Args:
        *blocks: a list of :py:class:`wildewidget.Block` (or subclass) instances to
            be added to this container

    Keyword Args:
        branding: A block that will be displayed at the top of the container.
            A good choice might be a :py:class:`LinkedImage` or :py:class:`Image`
        logo_width: The width for the logo image.  Any valid value
            for CSS ``width`` will be accepted.
        title: A title.  If ``logo`` is ``None``, this will be used in its
            place. If `logo` is not ``None``, this will be used as the image ``alt``
            attribute.
        contents_id: the CSS id of the menu container.  Typically you won't need
            to change this unless you have namespace collisions with other CSS
            ids on your page.

    """
    tag: str = 'aside'
    block: str = 'navbar'

    #: Valid values for ``navbar-expand-``. From
    #:`Navbar: How It Works <https://getbootstrap.com/docs/5.3/components/navbar/#how-it-works>`_
    VALID_BREAKPOINTS: List[str] = [
        'sm',
        'md',
        'lg',
        'xl',
        'xxl'
    ]
    #: Valid background colors.  Note that these are Tabler colors, not Bootstrap
    #: colors.  We use Tabler colors because Tabler also defines an appropriate
    #: foreground color for each background color.
    VALID_BACKGROUND_COLORS: List[str] = [
        'blue',
        'azure',
        'indigo',
        'purple',
        'pink',
        'red',
        'orange',
        'yellow',
        'lime',
        'green',
        'teal',
        'cyan',
        'white',
    ]

    #: Set to ``True`` to use a dark background instead of light
    dark: bool = False
    #: If :py:attr:`dark` is ``True``, set the background color. Default: ``#1d273b``
    background_color: Optional[str] = None
    #: the CSS id of the menu container.  Typically you won't need
    #: to change this unless you have namespace collisions with other CSS
    #: ids on your page.
    contents_id: str = 'sidebar-menu'
    #: A block that will be displayed at the top of the container.
    #: A good choice might be a :py:class:`LinkedImage` or :py:class:`Image`
    branding: Optional[Block] = None
    #: A list of blocks to include in our sidebar
    contents: Iterable[Block] = []
    #: The viewport size at which our menu container collapses to be hidden,
    #: requiring the hamburger menu to show
    hide_below_viewport: str = 'lg'
    #: The width of our actual navbar
    container_size: str = 'fluid'

    def __init__(
        self,
        *blocks: Block,
        contents_id: str = None,
        branding: Block = None,
        hide_below_viewport: str = None,
        container_size: str = None,
        dark: bool = None,
        background_color: str = None,
        **kwargs
    ):
        self.contents_id = contents_id if contents_id else self.contents_id
        self.hide_below_viewport = hide_below_viewport if hide_below_viewport else self.hide_below_viewport
        self.container_size = container_size if container_size else self.container_size
        self.dark = dark if dark is not None else self.dark
        self.background_color = background_color if background_color is not None else self.background_color
        if self.hide_below_viewport not in self.VALID_BREAKPOINTS:
            raise ValueError(
                f'"{self.hide_below_viewport}" is not a valid breakpoint size. '
                f'Choose from: {", ".join(self.VALID_BREAKPOINTS)}'
            )
        if self.background_color and self.background_color not in self.VALID_BACKGROUND_COLORS:
            raise ValueError(
                f'"{self.background_color}" is not a known color. '
                f'Choose from: {", ".join(self.VALID_BACKGROUND_COLORS)}'
            )

        super().__init__(**kwargs)
        # Set our hamburger menu breakpoint
        self.add_class(f'navbar-expand-{self.hide_below_viewport}')
        # light vs dark
        if self.dark:
            self.add_class('navbar-dark')
        # background color
        if self.background_color:
            self.add_class(f'bg-{self.background_color}')
            self.add_class(f'bg-{self.background_color}-fg')
        # Set our "role" attribute to make us more accessible
        self._attributes['role'] = 'navigation'
        #: Everything inside our sidebar lives in this inner container
        if self.container_size == 'fluid':
            margin_class = 'ms-0'
        else:
            margin_class = 'ms-auto'
        self.inner: Block = Container(size=self.container_size, css_class=margin_class)
        self.add_block(self.inner)
        #: This is the branding block at the start of the navbar
        self.branding: Block = branding if branding else deepcopy(self.branding)
        self.build_brand()
        # The menu toggler button for small viewports
        self.inner.add_block(NavigationTogglerButton(target=self.contents_id))
        #: This is the container for all menus
        self.menu_container: Block = CollapseWidget(css_id=self.contents_id, css_class='navbar-collapse')
        self.inner.add_block(self.menu_container)
        for block in self.contents:
            self.add_to_menu_section(block)

    def add_blocks(self) -> None:
        """
        Overrides :py:meth:`wildewidgets.widgets.base.Block.add_blocks`.

        We're overriding :py:meth:`wildewidgets.widgets.base.Block.add_blocks`
        here so that it does nothing because we need to add menus not to our
        top level tag content, but only to the menu section of ourselves,
        :py;attr:`menu_container`.

        :py:attr:`menu_container` doesn't exist yet when we run the constructor
        for :py:class:`wildewidgets.widgets.base.Block`, which is where
        ``add_blocks`` runs.
        """
        pass

    def build_brand(self) -> None:
        """
        Build our ``.navbar-brand`` block and add it to :py:attr:`inner`, our
        content container.  We're doing this in a method here so we can override
        it in subclasses.
        """
        if self.branding:
            # Add the .navbar-brand class to our branding block to make it work
            # properly within the .navbar
            self.branding.add_class('navbar-brand')

    def add_to_menu_section(self, block: Block) -> None:
        """
        Add a block to the menu specfic section of the sidebar,
        :py:attr:`menu_container`.  The menu specific section will be hidden and
        controlled by the hamburger menu when we drop below a specific viewport.

        Warning:
            Use this to add your blocks to this :py:class:`Navbar` instead of
            using :py:meth:`add_block`.

        Args:
            block: the block to add to the menu section
        """
        self.menu_container.add_block(block)

    def activate(self, text: str) -> bool:
        """
        Loop through all the :py:class:`Menu` blocks in
        :py:attr:`menu_container` and set the first menu item we find that
        matches ``text`` to be active.

        Args:
            text: the value to which to compare to menu items

        Returns:
            If we actually did set an item to be active, return
            ``True``, otherwise return ``False``
        """
        for block in self.menu_container.blocks:
            if isinstance(block, Menu):
                if block.activate(text):
                    return True
        return False


class TablerVerticalNavbar(Navbar):
    """
    Make this a Tabler vertical dark navbar.

    * Make the navbar vertical instead of horizontal
    * :py:attr:`dark` is always ``True``
    * Fix width of sidebar at 15rem, unless :py:attr:`wide` is ``True``, when we set it to 18rem.
    * CSS ``position`` is always ``fixed``.
    * Supply some open/close animations.

    Some caveats:

    * :py:attr:`container_size` is ignored

    Example:

        >>> branding = LinkedImage(
            src='/static/branding.png',
            alt='My Brand',
            url='https://example.com',
            width='100%`
        )
        >>> items = [MenuItem(text='One', url='/one'), ... ]
        >>> menu = TablerMenu(*items)
        >>> sidebar = TablerVerticalNavbar(menu, branding=branding)

    Keyword Args:
        wide: If ``True``, make the navbar width be 18rem instead of 15rem
    """
    block: str = 'navbar navbar-vertical'
    dark: bool = True

    #: Make the navbar 18rem wide instead of 15rem
    wide: bool = False

    def __init__(self, *args, wide: bool = None, **kwargs):
        self.wide = wide if wide is not None else self.wide
        super().__init__(*args, **kwargs)
        if self.wide:
            self._css_class += " navbar-wide"

    def build_brand(self) -> None:
        """
        Overrides :py:meth:`Navbar.build_brand`.

        Wrap our branding in an ``<h1>`` and give that ``<h1>`` the
        ``navbar-brand`` class because that's how Tabler does it.
        """
        brand_container = Block(
            self.branding,
            tag='h1',
            css_class=f'navbar-brand navbar-brand-autodark flex-grow-1 flex-{self.hide_below_viewport}-grow-0'
        )
        self.inner.add_block(brand_container)


class MenuHeading(Block):
    """
    A Tabler menu specific heading.  This is a heading within a :py:class:`Menu`
    that sepearates the actual menu items into groups.

    Typically, you won't use this directly, but instead it will be created for
    you from a :py:class:`MenuItem` specification when :py:attr:`MenuItem.url`
    is ``None`` and :py:attr:`MenuItem.items` is empty.

    Example:

        >>> heading = MenuHeading(text='My Heading')

    Kewyword Args:
        text: the text of the heading
    """

    block: str = 'nav-link nav-subtitle'
    css_class: str = 'nav-link my-1 fw-bold text-uppercase'

    #: The text of the heading
    text: Optional[str] = None

    def __init__(self, text: str = None, **kwargs):
        self.text = text if text else self.text
        super().__init__(**kwargs)
        self.add_block(self.text)


class NavItem(Block):
    """
    An entry in a :py:class:`Menu`, the top level menu class used in a
    :py:class:`Navbar` in the menu section.  This is a label with a link to a
    URL, with an optional icon preceding the label.

    Typically, you won't use this directly, but instead it will be created for
    you from a :py:class:`MenuItem` specification.

    If :py:attr:`url` and the ``url`` kwarg are ``None``, this will be a heading
    instead of an item that links to a URL.

    Examples:

        With keyword arguments::

            >>> icon = TablerMenuIcon(icon='target')
            >>> item = NavItem(text='Page', url='/page', icon=icon)

        With a :py:class:`MenuItem`::

            >>> menu_item = MenuItem(text='Page', url='/page', icon='target')
            >>> item2 = NavItem(item=menu_item)

        Adding a in-menu heading::

            >>> item3 = NavItem(text='My Heading')

    Kewyword Args:
        icon: Either the name of a Bootstrap icon, or a :py:class:`TablerMenuIcon` object
        text: The text for the item
        url: The URL for the item
        active: ``True`` if this represents the page we're currently on
        item: a :py:class:`MenuItem`

    Raises:
        ValueError: one or more of the settings failed validation
    """

    tag: str = 'li'
    block: str = 'nav-item'

    #: Either the name of a Bootstrap icon, or a :py:class:`TablerMenuIcon`
    #: object
    icon: Optional[Union[str, TablerMenuIcon]] = None
    #: The text for the item.
    text: Optional[str] = None
    #: The URL for the item.
    url: Optional[str] = None

    def __init__(
        self,
        text: str = None,
        icon: Union[str, TablerMenuIcon] = None,
        url: str = None,
        active: bool = False,
        item: MenuItem = None,
        **kwargs
    ):
        self.active: bool = active
        if item and (text or icon or url or active):
            raise ValueError('Specify "item" or ("text", "icon", "url", "active"), but not both')
        if item:
            self.text = item.text
            self.icon = item.icon if item.icon else deepcopy(self.icon)
            self.url = item.url if item.url else self.url
            self.active = item.active
        else:
            self.text = text if text else self.text
            self.icon = icon if icon else self.icon
            self.url = url if url else self.url
            if not self.text:
                raise ValueError('"text" is required as either a class attribute or keyword arg')
        super().__init__(**kwargs)
        if self.active:
            self.add_class('active')
        icon_block: Block = None
        if self.icon:
            if isinstance(self.icon, TablerMenuIcon):
                icon_block = self.icon
            else:
                icon_block = TablerMenuIcon(icon=self.icon)
        contents: Block
        if self.url:
            contents = Link(url=self.url, css_class='nav-link')
            if icon_block:
                contents.add_block(icon_block)
            contents.add_block(self.text)
        else:
            contents = MenuHeading(text=self.text)
        self.add_block(contents)


# Submenus:

class ClickableNavDropdownControl(Block):
    """
    This is a variation on :py:class:`NavDropdownControl` for the cases when the
    text that controls the open and close of the related
    :py:class:`DropdownMenu` is also a link that should be able to be clicked
    separately.

    To implement that, this is a ``<div>`` with two different links in it:

    * A first link that link that links our :py:attr:`text` to :py:attr:`url`,
      optionally with an icon.
    * A second link that is just the up/down arrow for the dropdown control.
      Clicking this is what opens the submenu with CSS id :py:attr:`menu_id`.

    Examples:

        No icon:

        >>> control = ClickableNavDropdownControl(
            'the-menu-id',
            text='My Text',
            url='/destination'
        )

        With an icon:

        >>> control2 = ClickableNavDropdownControl(
            'the-menu-id',
            text='My Text',
            url='/destination',
            icon='arrow-down-square-fill'
        )

        With a :py:class:`TablerMenuIcon`:

        >>> arrow_icon = TablerMenuIcon(icon='arrow-down-square-fill')
        >>> control3 = ClickableNavDropdownControl(
            'the-menu-id',
            text='My Text',
            url='/destination',
            icon=arrow_icon
        )

    Args:
        menu_id: The CSS Id to of the dropdown menu that this controls.

    Keyword Args:
        icon: either the name of a Bootstrap icon, or a :py:class:`TablerMenuIcon`
            class or subclass
        text: The label for the dropdown control
        url: The URL for the item.  For Django urls, you will typically do something like
            ``reverse('myapp:view')`` or ``reverse_lazy('myapp:view')``

    Raises:
        ValueError: no ``text`` was supplied
    """

    block: str = 'nav-item--clickable'

    #: Either the name of a Bootstrap icon, or a :py:class:`TablerMenuIcon`
    #: class or subclass
    icon: Optional[Union[str, TablerMenuIcon]] = None
    #: The actual name of the dropdown
    text: Optional[str] = None
    #: The URL to associated with the control
    url: Optional[str] = None

    def __init__(
        self,
        menu_id: str,
        text: str = None,
        icon: Union[str, TablerMenuIcon] = None,
        url: str = None,
        active: bool = False,
        **kwargs
    ):
        #: If this is ``True``, this control itself is active, but nothing
        #: in the related :py:class:`DropdownMenu` is
        self.active: bool = active
        self.text = text if text else self.text
        self.icon = icon if icon else deepcopy(self.icon)
        self.url = url if url else self.url
        if not self.url:
            raise ValueError('"url" is required as either a class attribute of a keyword arg')
        if not self.text:
            raise ValueError('"text" is required as either a class attribute of a keyword arg')
        super().__init__(**kwargs)
        # These classes make the link + control look right
        for klass in ['d-flex', 'flex-row', 'justify-content-between', 'align-items-center']:
            self.add_class(klass)
        self.link = Link(url=self.url, name='nav-link')
        # make the clickable link
        if self.icon:
            self.link.add_block(TablerMenuIcon(icon=self.icon))
        self.link.add_block(self.text)
        # make the actual dropdown control
        self.control = Link(
            css_class='nav-link dropdown-toggle',
            role='button',
            data_attributes={
                'toggle': 'dropdown-ww',  # This data-bs-toggle is targeted by our own javascript
                'target': f'#{menu_id}'
            },
            aria_attributes={
                'expanded': 'false'
            }
        )
        self.add_block(self.link)
        self.add_block(self.control)
        if self.active:
            self.add_class('active')

    def expand(self) -> None:
        """
        Set our ``aria-expanded`` attribute to ``true``.
        """
        self.control._aria_attributes['expanded'] = 'true'

    def collapse(self) -> None:
        """
        Set our ``aria-expanded`` attribute to ``false``.
        """
        self.control._aria_attributes['expanded'] = 'false'


class NavLinkToggle(Link):
    """
    This is a control for a
    :py:class:`wildewidgets.widgets.structure.CollapseWidget` that is some text
    with an open/closed indicator.  Clicking on the text opens or closes the
    ``CollapseWidget``.

    This differs from :py:class:`wildewidgets.widgets.buttons.CollapseButton` in that
    it doesn't have button styling, and has the open/closed indicator.

    Keyword Args:
        icon: Either the name of a Bootstrap icon, or a :py:class:`TablerMenuIcon` object
        text: The text for the item
        active: ``True`` if this represents the page we're currently on
        collapse_id: the CSS id of the :py:class:`wildewidgets.widgets.structure.CollapseWidget`
    """

    block: str = 'nav-link'
    name: str = 'nav-link-toggle'
    data_attributes: Dict[str, str] = {
        'toggle': 'collapse',
    }
    aria_attributes: Dict[str, str] = {
        'expanded': 'false'
    }

    #: Either the name of a Bootstrap icon, or a :py:class:`TablerMenuIcon`
    #: class or subclass
    icon: Optional[Union[str, TablerMenuIcon]] = None
    #: The title for the link
    text: Optional[str] = None
    #: The CSS id of the Collapse that we control
    collapse_id: Optional[str] = None

    def __init__(
        self,
        text: str = None,
        icon: Union[str, TablerMenuIcon] = None,
        active: bool = False,
        collapse_id: str = None,
        **kwargs
    ):
        #: This item is active, but nothing in the related :py:class:`DropdownMenu` is
        self.active: bool = active
        self.text = text if text else self.text
        self.icon = icon if icon else deepcopy(self.icon)
        self.collapse_id = collapse_id if collapse_id else self.collapse_id
        if self.collapse_id is None:
            raise self.RequiredAttrOrKwarg('collapse_id')
        if not self.text:
            raise self.RequiredAttrOrKwarg('text')
        super().__init__(role='button', **kwargs)
        self._data_attributes['target'] = self.collapse_id
        # these classes cause the up/down arrow to be nicely separated from the text
        self.add_class('d-flex')
        self.add_class('flex-row')
        self.add_class('justify-content-between')
        if self.icon:
            if isinstance(self.icon, TablerMenuIcon):
                icon_block = self.icon
            else:
                icon_block = TablerMenuIcon(icon=self.icon)
            self.add_block(icon_block)
        self.add_block(self.text)
        if self.active:
            self.add_class('active')

    def expand(self) -> None:
        """
        Set our ``aria-expanded`` attribute to ``true``.
        """
        self._aria_attributes['expanded'] = 'true'

    def collapse(self) -> None:
        """
        Set our ``aria-expanded`` attribute to ``false``.
        """
        self._aria_attributes['expanded'] = 'false'


class NavDropdownControl(Link):
    """
    This is a dropdown control that opens a submenu from within either a
    :py:class:`Menu` or a :py:class`DropdownMenu` within a :py:class:`Menu`.  It
    consists of a label with optional icon in front, plus a arrow that toggles
    direction when the menu opens and closes.

    Examples:

        No icon:

        >>> control = NavDropdownControl(text='My Control')

        With an icon:

        >>> control2 = NavDropdownControl(text='My Control', icon='arrow-down-square-fill')

        With a :py:class:`TablerMenuIcon`:

        >>> arrow_icon = TablerMenuIcon(icon='arrow-down-square-fill')
        >>> control3 = NavDropdownControl(text='My Control', icon=arrow_icon)

    Keyword Args:
        icon: either the name of a Bootstrap icon, or a :py:class:`TablerMenuIcon`
            class or subclass
        text: The label for the dropdown control
        button_id: The CSS Id to assign to this button.  We need this to tie the
            button to the actual :py:class:`DropdownItem`

    Raises:
        ValueError: no ``text`` was supplied
    """

    block: str = 'nav-link'
    name: str = 'dropdown-toggle'
    data_attributes: Dict[str, str] = {
        'toggle': 'dropdown',
        'auto-close': 'true'
    }
    aria_attributes: Dict[str, str] = {
        'expanded': 'false'
    }
    #: Either the name of a Bootstrap icon, or a :py:class:`TablerMenuIcon`
    #: class or subclass
    icon: Optional[Union[str, TablerMenuIcon]] = None
    #: The actual name of the dropdown
    text: Optional[str] = None
    #: The CSS Id to assign to this button.  We need this to tie the button
    #: to the actual :py:class:`TablerDropdownItem`
    button_id: Optional[str] = None

    def __init__(
        self,
        text: str = None,
        icon: Union[str, TablerMenuIcon] = None,
        active: bool = False,
        button_id: str = None,
        **kwargs
    ):
        #: This item is active, but nothing in the related :py:class:`DropdownMenu` is
        self.active: bool = active
        self.text = text if text else self.text
        self.icon = icon if icon else deepcopy(self.icon)
        self.button_id = button_id if button_id else self.button_id
        if not self.text:
            raise self.RequiredAttrOrKwarg('text')
        if not self.button_id:
            raise self.RequiredAttrOrKwarg('button_id')
        super().__init__(css_id=self.button_id, role='button', **kwargs)
        if self.icon:
            if isinstance(self.icon, TablerMenuIcon):
                icon_block = self.icon
            else:
                icon_block = TablerMenuIcon(icon=self.icon)
            self.add_block(icon_block)
        self.add_block(self.text)
        if self.active:
            self.add_class('active')

    def expand(self) -> None:
        """
        Set our ``aria-expanded`` attribute to ``true``.
        """
        self._aria_attributes['expanded'] = 'true'

    def collapse(self) -> None:
        """
        Set our ``aria-expanded`` attribute to ``false``.
        """
        self._aria_attributes['expanded'] = 'false'


class DropdownItem(Link):
    """
    An entry in a :py:class:`DropdownMenu`, a submenu class used in a
    :py:class:`NavDropdownItem` of a :py:class:`Menu`.  This is a
    label with a link to a URL, with an optional icon preceding the label.

    Typically, you won't use this directly, but instead it will be created for
    you from a :py:class:`MenuItem` specification when :py:attr:`MenuItem.url`
    is not ``None``.

    Examples:

        >>> icon = TablerMenuIcon(icon='target')
        >>> item = DropdownItem(text='Page', url='/page', icon=icon)

        >>> menu_item = MenuItem(text='Page', url='/page', icon='target')
        >>> item = DropdownItem(item=menu_item)

    Kewyword Args:
        icon: Either the name of a Bootstrap icon, or a :py:class:`TablerMenuIcon` object
        text: The text for the item
        active: ``True`` if this represents the page we're currently on
        item: a :py:class:`MenuItem`

    Raises:
        ValueError: one or more of the arguments failed validation
    """
    block: str = 'dropdown-item'

    #: this is either the name of a bootstrap icon, or a :py:class:`TablerMenuIcon`
    #: class or subclass
    icon: Optional[Union[str, TablerMenuIcon]] = None
    #: The text for the item.
    text: Optional[str] = None

    def __init__(
        self,
        text: str = None,
        icon: str = None,
        active: bool = False,
        item: MenuItem = None,
        **kwargs
    ):
        # Does this item represent the page we're on?
        self.active: bool = active
        if item and (text or icon or kwargs.get('url', None)):
            raise ValueError('Specify "item" or ("text", "icon", "url"), but not both')
        if item:
            self.text = item.text
            self.icon = item.icon if item.icon else self.icon
            if item.url:
                kwargs['url'] = item.url
            self.active = item.active
        else:
            self.text = text if text else self.text
            self.icon = icon if icon else self.icon
        if not self.text:
            raise ValueError('"text" is required as either a class attribute or keyword arg')
        if not self.url:
            raise ValueError('"url" is required as either a class attribute or keyword arg')
        super().__init__(**kwargs)
        if self.active:
            self.add_class('active')
        icon_block: Block = None
        if self.icon:
            icon_block = TablerMenuIcon(icon=self.icon, css_class='text-white')
        if icon_block:
            self.add_block(icon_block)
        self.add_block(self.text)


# TODO: tabler dropdown divider

class DropdownMenu(Block):
    """
    A `Tabler dropdown menu <https://preview.tabler.io/docs/dropdowns.html>`_.

    Typically, you won't use this directly, but instead it will be created for
    you from a :py:class:`MenuItem` specification when :py:attr:`MenuItem.url`
    is not ``None``.

    Examples:

        >>> items = [
            MenuItem(text='One', url='/one', icon='1-circle'),
            MenuItem(text='Two', url='/two', icon='2-circle'),
            MenuItem(text='Three', url='/three', icon='3-circle'),
        ]
        >>> button = NavDropdownControl(
            text='My Dropdown Menu',
            icon='arrow-down-square-fill',
            button_id='my-button'
        )
        >>> menu = DropdownMenu(*items, button_id=button.button_id)

    Args:
        *items: the list of :py:class:`MenuItem` objects to insert into
            this menu

    Keyword Args:
        button_id: it CSS id for the button

    Raises:
        ValueError: one or more of the settings failed validation
    """

    block: str = 'dropdown-menu'

    #: A list of :py:class:`MenuItem` objects to add to this dropdown menu
    items: Iterable[MenuItem] = []
    #: The id of the dropdown-toggle button that controls this menu
    button_id: Optional[str] = None

    def __init__(
        self,
        *items: MenuItem,
        button_id: str = None,
        **kwargs
    ):
        self.button_id = button_id if button_id else self.button_id
        if items:
            self.items: Iterable[MenuItem] = items
        else:
            self.items = deepcopy(self.items)
        super().__init__(**kwargs)
        if not self.button_id and not self._css_id:
            raise ValueError('Either "button_id" or "css_id" are required as either class attributes of keyword args')
        if self.button_id:
            self._aria_attributes['labelledby'] = self.button_id
        for item in items:
            self.add_item(item=item)

    def add_item(
        self,
        text: str = None,
        url: str = None,
        icon: Union[str, TablerMenuIcon] = None,
        active: bool = False,
        item: MenuItem = None
    ) -> None:
        """
        Add a new item to this :py:class:`DropdownMenu`.

        Kewyword Args:
            icon: Either the name of a Bootstrap icon, or a :py:class:`TablerMenuIcon` object
            text: The text for the item
            url: The URL for the item
            active: ``True`` if this represents the page we're currently on
            item: a :py:class:`MenuItem`

        Raises:
            ValueError: one or more of the settings failed validation
        """
        if item and (text or icon or url or active):
            raise ValueError('Specify "item" or ("text", "icon", "url"), but not both')
        if not item:
            if text:
                raise ValueError('"text" is required if "item" is not provided')
            item = MenuItem(text=cast(str, text), url=url, icon=icon, active=active)
        if item.items:
            self.add_block(NavDropdownItem(
                *item.items,
                text=item.text,
                url=item.url,
                icon=item.icon
            ))
        else:
            self.add_block(DropdownItem(item=item))

    def show(self) -> None:
        """
        Force this dropdown menu to be shown.
        """
        self.add_class('show')

    def hide(self) -> None:
        """
        Force this dropdown menu to be hidden.
        """
        self.remove_class('show')


class NavDropdownItem(Block):
    """
    An item in a :py:class:`Menu` that opens a dropdown submenu.

    Typically, you won't use this directly, but instead it will be created for
    you from a :py:class:`MenuItem` specification when :py:attr:`MenuItem.items`
    is not empty.

    Examples:

        >>> sub_items = [
            MenuItem(text='One', url='/one', icon='1-circle'),
            MenuItem(text='Two', url='/two', icon='2-circle'),
            MenuItem(text='Three', url='/three', icon='3-circle'),
        ]
        >>> item = NavDropdownItem(*sub_items, text='My Submenu', icon='target')
        >>> menu = Menu(item)


    Args:
        *items: the list of :py:class:`MenuItem` objects to insert into
            this menu

    Keyword Args:
        text: the text for the menu item
        icon: this is either the name of a Bootstrap icon, or a
            :py:class:`TablerMenuIcon` class or subclass

    Raises:
        ValueError: one or more of the settings failed validation
    """

    tag: str = 'li'
    block: str = 'nav-item dropdown'

    #: this is either the name of a bootstrap icon, or a :py:class:`TablerMenuIcon`
    #: class or subclass
    icon: Optional[Union[str, TablerMenuIcon]] = None
    #: The actual name of the dropdown
    text: Optional[str] = None
    #: The URL for the control text.  Use this if you want :py:attr:`text` to be
    #: clickable separately from opening the dropdown menu
    url: Optional[str] = None
    #: The list of items in this dropdown menu
    items: Iterable[MenuItem] = []

    def __init__(
        self,
        *items: MenuItem,
        text: str = None,
        icon: str = None,
        url: str = None,
        active: bool = False,
        **kwargs
    ):

        #: The control for opening the dropdown menu is active, but nothing in the
        #: related :py:class:`DropdownMenu` is active
        self.active = active
        #: The control that opens and closes :py:attr:`menu`
        self.control: Union[NavDropdownControl, ClickableNavDropdownControl]
        #: The :py:class:`DropdownMenu`  that :py:attr:`control` opens
        self.menu: DropdownMenu
        self.text = text if text else self.text
        self.url = url if url else self.url
        self.icon = icon if icon else deepcopy(self.icon)
        if not self.text:
            raise ValueError('"text" is required as either a class attribute of a keyword arg')
        if items:
            self.items: Iterable[MenuItem] = items
        else:
            self.items = deepcopy(self.items)
        super().__init__(**kwargs)
        if self.url:
            # We need to be able to click on the control to get to a page
            menu_id: str = f'nav-menu-{self.text.lower()}'
            menu_id = re.sub('[ ._]', '-', menu_id)
            self.menu = DropdownMenu(*self.items, css_id=menu_id)
            self.control  = (
                ClickableNavDropdownControl(
                    menu_id=menu_id,
                    text=self.text,
                    icon=self.icon,
                    url=self.url,
                    active=self.active
                )
            )
            # FIXME: should we set up aria-labelledby on the menu to point to the control?
        else:
            # We don't need to be able to click on the control to get to a page
            button_id: str = f'nav-item-{self.text.lower()}'
            button_id = re.sub('[ ._]', '-', button_id)
            self.control = NavDropdownControl(
                button_id=button_id,
                text=self.text,
                icon=self.icon,
                active=self.active
            )
            self.menu = DropdownMenu(*self.items, button_id=button_id)
        self.add_block(self.control)
        self.add_block(self.menu)

    def show(self) -> None:
        """
        Show our :py:attr:`menu`.
        """
        self.control.expand()
        self.menu.show()

    def hide(self) -> None:
        """
        Hide our :py:attr:`menu`.
        """
        self.control.collapse()
        self.menu.hide()

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """
        Overrides :py:meth:`wildewidgets.widgets.base.Block.get_context_data`.

        Show our menu if either :py:attr:`active` is ``True`` or any item in our
        :py:attr:`menu` is active.  We do this here instead of in our constructor
        so that any menu item activation that happens after instance construction
        time is accounted for.
        """
        is_active: bool = self.active or any(item.is_active for item in self.items)
        if is_active:
            self.show()
        else:
            self.hide()
        return super().get_context_data(**kwargs)


class Menu(Block):
    """
    A ``<div>`` with an optional title and a  `Bootstrap ``ul.navbar-nav``
    <https://getbootstrap.com/docs/5.2/components/navbar/>`_ for use in a
    :py:class:`Navbar`.

    Use this in any of these ways:

    * Subclass :py:class:`Menu` and define :py:attr:`items`
    * Pass in the ``items`` kwargs to the constructor
    * Add items with :py:meth:`add_item`
    * Subclass :py:class:`Menu`, define :py:attr:`items`, and add additional items with
      :py:meth:`add_item`

    Examples:

        Subclassing::

            class MyMenu(Menu):

                items = [
                    MenuItem(text='One', url='/one', icon='1-circle'),
                    MenuItem(text='Two', url='/two', icon='2-circle'),
                    MenuItem(text='Three', url='/three', icon='3-circle'),
                ]

        Constructor::

            >>> menu = Menu(
                MenuItem(text='One', url='/one', icon='1-circle'),
                MenuItem(text='Two', url='/two', icon='2-circle'),
                MenuItem(text='Three', url='/three', icon='3-circle'),
            )

        ``Menu.add_item``::

            >>> menu = Menu()
            >>> menu.add_item(MenuItem(text='One', url='/one', icon='1-circle'))
            >>> menu.add_item(MenuItem(text='Two', url='/two', icon='2-circle'))
            >>> menu.add_item(MenuItem(text='Three', url='/three', icon='3-circle'))

    Args:
        *items: the list of :py:class:`MenuItem` objects to insert into
            this menu

    Keyword Args:
        title: the title for this menu
        title_tag: the HTML tag to use for the title
        title_css_classes: CSS classes to apply to the title

    Raises:
        ValueError: one or more of the settings failed validation
    """

    tag: str = 'div'
    block: str = 'menu'
    css_class: str = 'me-1'

    #: The list of items in this menu
    items: Iterable[MenuItem] = []
    #: The title for this menu
    title: Optional[str] = None
    #: The HTML tag for this title
    title_tag: str = 'h4'
    #: CSS classes to apply to the title
    title_css_classes: str = ''

    def __init__(
        self,
        *items: MenuItem,
        title: str = None,
        title_tag: str = None,
        title_css_classes: str = None,
        **kwargs
    ):
        self.title = title if title else self.title
        self.title_tag = title_tag if title_tag else self.title_tag
        self.title_css_classes = title_css_classes if title_css_classes else self.title_css_classes
        if items:
            self._items: List[MenuItem] = list(items)
        else:
            self._items = list(deepcopy(self.items))
        super().__init__(**kwargs)

    def get_content(self, **kwargs) -> str:
        """
        Actually build out the menu from our list of :py:class:`MenuItems`.  We do
        this in :py:meth:`get_content` instead of in ``__init__`` so that we catch
        any menu items added via :py:meth:`add_item` after instantiation.
        """
        self.build_menu(self._items)
        return super().get_content(**kwargs)

    def build_menu(self, items: Iterable[MenuItem]) -> None:
        """
        Recurse through ``items`` and build out our menu and any submenus.

        For each ``item`` in ``items``, if ``item.items`` is not empty, add a
        submenu, otherwise add simple item.

        Args:
            items: the list of menu items to add to the list
        """
        ul = Block(tag='ul', css_class='navbar-nav')
        if self.title:
            self.add_block(Block(self.title, tag=self.title_tag, css_class=self.title_css_classes + ' menu-title'))
        self.add_block(ul)
        for item in items:
            if item.items:
                ul.add_block(NavDropdownItem(
                    *item.items,
                    text=item.text,
                    icon=item.icon,
                    url=item.url,
                    active=item.active
                ))
            else:
                ul.add_block(NavItem(item=item))

    def add_item(self, item: MenuItem) -> None:
        """
        Add a single :py:class:`MenuItem` to ourselves.

        Args:
            item: the menu item to add to ourselves.
        """
        self._items.append(item)

    def activate(self, text: str) -> bool:
        """
        If ``text`` is not a URL or path, Set :py:attr:`MenuItem.active` to
        ``True`` for the first item we find in our :py:attr:`items` (searching
        recursively) whose :py:attr:`MenuItem.text` matches ``text``.

        If ``text`` is a URL or path, Set :py:attr:`MenuItem.active` to
        ``True`` for the first item we find in our :py:attr:`items` (searching
        recursively) whose :py:attr:`MenuItem.url` matches ``text``.

        Args:
            text: the text to search for among our :py:attr:`items`

        Returns:
            If we found a match, return ``True``, otherwise return ``False``.
        """
        for item in self._items:
            if item.set_active(text):
                return True
        return False


# ==============================
# View mixins
# ==============================

class NavbarMixin:
    """
    This is a Django class based view mixin that offers methods and attributes
    for managing how your :py:class:`Navbar` classes get rendered in your template.

    To use :py:class:`MenuMixin`, you must, in the template for your view,
    render the ``menu`` and ``submenu`` context parameters with the
    ``wildewidgets`` template tag.  These will be the :py:class:`Navbar`
    subclasses that :py:meth:`MenuMixin.get_context_data` adds to the template
    context.   For example::

        <html>
          <head>
            {# wildewdigets css and js requirements #}
          </head>
          <body>
            {% wildewidgets menu %}
            <div class="page">
                ...
                {% wildewidgets submenu %}
                ...
            </div>
          </body>
        </html

    Example:

        This is the most basic example of how to use :py:class:`NavbarMixin` to
        manage a :py:class:`Navbar` with a :py:class:`Menu` inside it and have
        one of the menu items be marked as active::

            from django.views import View
            from django.urls import reverse_lazy
            from wildewidgets import (
                TablerVerticalNavbar,
                Menu,
                MenuItem,
                NavbarMixin
            )

            class MainMenu(Menu):
                items = [
                    MenuItem(
                        text='Projects',
                        icon='bookshelf',
                        url=reverse_lazy('myapp:project--list')
                    ),
                    MenuItem(
                        text='Users',
                        icon='users',
                        url=reverse_lazy('myapp:users--list')
                    )
                ]

            class NavigationSidebar(TablerVerticalNavbar):
                branding = LinkedImage(
                    image_src=static("myapp/images/logo.png"),
                    image_width='100%',
                    image_alt="My App",
                    url="/"
                )

                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.add_to_menu_section(MainMenu())


            class MyView(NavbarMixin, View):

                navbar_class = NavigationSidebar
                menu_item = 'Projects'

                ...

        This defines our navbar ``NavigationSidebar``, adds ``MainMenu` to it,
        assigns it as our main menu (via ``MyView.navbar_class``), and activates
        the "Projects" item in the main menu (via ``MyView.menu_item``).

        If we wanted to have a secondary navbar also, just define a new
        :py:class:`Navbar` subclass, with a ``secondary_menu_item``::

            class SecondaryMenu(Menu):
                ...

            class ContextualNavbar(Navbar):
                ...

            class MyView(NavbarMixin, View):

                navbar_class = NavigationSidebar
                menu_item = 'Projects'
                secondary_navbar_class = ContextualNavbar
                secondary_menu_item = 'The item'

                ...

    """

    #: The :py:class:`Navbar`` subclass that acts as our primary navigation
    navbar_class: Type[Navbar] = Navbar
    #: The text or URL of an item in one of our :py:attr:`navbar_class` menus to
    #: set active
    menu_item: Optional[str] = None
    #: The :py:class:`Navbar` subclass that holds our secondary menus
    secondary_navbar_class: Optional[Type[Navbar]] = None
    #: The text or URL of an item in one of our
    #: :py:attr:`secondary_navbar_class` menus to set active
    secondary_menu_item: Optional[str] = None

    def get_navbar_class(self) -> Type[Navbar]:
        """
        Return the :py:class:`Navbar` subclass for the main menu.  Overriding
        this will allow you to programmatically determine your at view time.

        Returns:
            The class of the :py:class:`Navbar` subclass to use for our
            main menu.
        """
        return self.navbar_class

    def get_menu_item(self) -> Optional[str]:
        """
        Return the text or URL of an item to set active among the menus
        in our main :py:class:`Navbar` class.

        Returns:
            The class of the :py:class:`Navbar` subclass to use for our
            main menu.
        """
        return self.menu_item

    def get_navbar(self) -> Navbar:
        """
        Instantiate and return our :py:class:`Navbar` subclass for our
        main navbar.

        Returns:
            The instantiated :py:class:`Navbar` subclass instance to use for our
            main navbar.
        """
        navbar_class = self.get_navbar_class()
        if not navbar_class:
            raise ImproperlyConfigured('"navbar_class" must not be None')
        return navbar_class()

    def get_secondary_navbar_class(self) -> Optional[Type[Navbar]]:
        """
        Return our :py:class:`Navbar` subclass for the secondary navbar.

        Returns:
            The class of the :py:class:`Navbar` subclass to use for our
            secondary navbar, if any.
        """
        return self.secondary_navbar_class

    def get_secondary_menu_item(self) -> Optional[str]:
        """
        Return the text of an item to set active in our secondary menu
        """
        return self.secondary_menu_item

    def get_secondary_navbar(self) -> Optional[Navbar]:
        """
        Instantiate and return our :py:class:`Navbar` subclass for our
        secondary navbar.

        Returns:
            The instantiated :py:class:`Navbar` subclass instance to use for our
            secondary menu, if any.
        """
        secondary_navbar_class = self.get_secondary_navbar_class()
        if secondary_navbar_class:
            # pylint is saying that secondary_navbar_class is not callable, which is not true
            return secondary_navbar_class()  # pylint: disable=not-callable
        return None

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """
        Add our main navbar and our secondary navbar (if we have one) to the context
        data for our view as the ``menu`` and ``submenu`` kwargs, respectively

        Returns:
            The updated context data.
        """
        kwargs['menu'] = self.get_navbar()
        if menu_item := self.get_menu_item():
            kwargs['menu'].activate(menu_item)
        secondary_navbar = self.get_secondary_navbar()
        if secondary_navbar:
            kwargs['submenu'] = secondary_navbar
            if submenu_item := self.get_secondary_menu_item():
                secondary_navbar.activate(submenu_item)
        return super().get_context_data(**kwargs)  # type: ignore
