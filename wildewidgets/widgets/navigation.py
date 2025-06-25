from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Final

from django.core.exceptions import ImproperlyConfigured

from .base import Block, Container, Link, OrderedList
from .icons import TablerMenuIcon
from .structure import CollapseWidget

if TYPE_CHECKING:
    from collections.abc import Iterable

#: A regular expression that matches a valid URL path.
#: A valid URL path starts with a slash and does not contain whitespace.
path_validator_re = re.compile(r"^/\S+$", re.IGNORECASE)


#: A regular expression that matches a valid URL.
#: A valid URL starts with http:// or https://, followed by a domain or IP address,
#: and may include a port number and path.
#:
#: * A valid URL may also be a localhost URL.
#: * The domain must be a valid top-level domain or a valid IP address.
#: * The port number, if present, must be a valid integer.
#: * The path, if present, must not contain whitespace.
#: * The URL may end with a slash or a query string.
#:
#: Note: This regex is not perfect and may not match all valid URLs, but it should
#:       match most common cases.  It is designed to be simple and easy to read.
#:       If you need a more complex URL validation, consider using a library like
#:       `validators <https://pypi.org/project/validators/>`_ or
#:       :py:class:`django.core.validators.URLValidator`.
url_validator_re = re.compile(
    r"^(?:http)s?://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...  # noqa: E501
    r"localhost|"  # localhost...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)


# ==============================
# Functions
# ==============================


def is_url(text: str) -> bool:
    """
    Check if a string appears to be a URL or path.

    This function uses regular expressions to determine if the provided text
    matches patterns for either a relative path (starting with slash) or
    an absolute URL (with protocol).

    Args:
        text: The string to check

    Returns:
        bool: True if the text looks like a URL or path, False otherwise

    Examples:
        >>> is_url("/some/path")
        True
        >>> is_url("https://example.com")
        True
        >>> is_url("not a url")
        False

    """
    return bool(path_validator_re.search(text) or url_validator_re.search(text))


# ==============================
# Dataclasses
# ==============================


@dataclass
class MenuItem:
    """
    A menu item definition for use in :py:class:`Menu` and related components.

    This dataclass simplifies the creation of complex menu structures by allowing
    nested hierarchies of menu items. It's used by various menu components to
    create navigation structures without having to manually build the DOM elements.

    The only required attribute/keyword argument is `text`. If `url` is not
    provided, the item will be rendered as a section title in menus. If `items`
    is not empty, the item will be rendered as a dropdown or submenu.

    Attributes:
        text: The display text for the menu item (required)
        icon: Optional icon to display next to the text (either a string name of
            a Bootstrap icon or a TablerMenuIcon instance)
        url: Optional URL the menu item should link to
        items: Optional list of nested MenuItem objects for dropdown menus
        active: Whether this item should be highlighted as active/current

    Examples:
        Basic menu item:

        .. code-block:: python

            from wildewidgets import MenuItem

            item = MenuItem(text="Home", url="/", icon="house")

        Section header (no URL):

        .. code-block:: python

            header = MenuItem(text="Management")

        Dropdown menu:

        .. code-block:: python

            from wildewidgets import MenuItem

            dropdown = MenuItem(
                text="Settings",
                icon="gear",
                items=[
                    MenuItem(text="Profile", url="/profile"),
                    MenuItem(text="Preferences", url="/prefs")
                ]
            )

    """

    #: The text for the item.  If ``url`` is not defined, this will define
    #: a heading within the menu
    text: str
    #: this is either the name of a bootstrap icon, or a :py:class:`Block`
    icon: str | Block | None = None
    #: The URL for the item.  For Django urls, you will typically do something like
    #: ``reverse('myapp:view')`` or ``reverse_lazy('myapp:view')``
    url: str | None = None
    #: a submenu under this menu item
    items: list[MenuItem] = field(default_factory=list)
    #: Is this the page we're currently on?
    active: bool = False

    @property
    def is_active(self) -> bool:
        """
        Check if this menu item or any of its children is marked as active.

        This property recursively checks the active state of this item and all its
        children. It returns True if either this item is active or any child item
        is active.

        Returns:
            bool: True if this item or any of its child items is active

        """
        status = self.active
        if not status:
            return any(item.is_active for item in self.items)
        return status

    def set_active(self, text: str) -> bool:
        """
        Mark this item as active if it matches the given text or URL.

        This method recursively checks this item and its children for a match:

        - If `text` appears to be a URL, it's compared against the item's `url`
        - If `text` is not a URL, it's compared against the item's `text`
        - If no match is found, the method is called recursively on all child items

        Args:
            text: The text or URL to match against

        Returns:
            bool: True if this item or any of its children was set to active

        Examples:
            .. code-block:: python

                from wildewidgets import MenuItem

                menu_item = MenuItem(text="Products", url="/products/")
                menu_item.set_active("/products/")  # Match by URL
                menu_item.set_active("Products")    # Match by text

        """
        target = self.url if is_url(text) else self.text
        if target == text:
            self.active = True
            return True
        self.active = False
        return any(item.set_active(text) for item in self.items)


@dataclass
class BreadcrumbItem:
    """
    A single item in a breadcrumb navigation trail.

    This dataclass represents one segment in a breadcrumb navigation component,
    containing a title and an optional URL. Items without URLs typically represent
    the current page.

    Attributes:
        title: Display text for the breadcrumb item
        url: Optional URL the breadcrumb item should link to. If None, the item
            will be displayed as plain text (typically the current page).

    Examples:
        >>> home = BreadcrumbItem(title="Home", url="/")
        >>> section = BreadcrumbItem(title="Products", url="/products/")
        >>> current = BreadcrumbItem(title="Product Details")

    """

    #: The title for the breadcrumb
    title: str
    #: The optional URL for the breadcrumb
    url: str | None = None


class BreadcrumbBlock(Block):
    """
    A Bootstrap breadcrumb navigation component.

    This widget creates a breadcrumb trail showing the hierarchical path to the current
    page. It's typically used to show navigation context and allow users to navigate
    back up the hierarchy.

    You can create a base BreadcrumbBlock with common starting points (like 'Home')
    and then extend it in specific views to add additional breadcrumbs for deeper pages.

    Attributes:
        tag: HTML tag for the container ('nav')
        aria_attributes: Accessibility attributes for the breadcrumb component
        title_class: CSS classes to apply to each breadcrumb title
        items: Base list of breadcrumb items to always include
        breadcrumbs: The OrderedList that holds the actual breadcrumb items

    Examples:
        Creating a base breadcrumb class:

        .. code-block:: python

            from wildewidgets import BreadcrumbBlock

            class BaseBreadcrumbs(BreadcrumbBlock):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.add_breadcrumb('Home', url='/home')

        Using breadcrumbs in a view:

        .. code-block:: python

            def get_context_data(self, **kwargs):
                kwargs = super().get_context_data(**kwargs)
                breadcrumbs = BaseBreadcrumbs()
                breadcrumbs.add_breadcrumb('Products', url='/products')
                breadcrumbs.add_breadcrumb('Product Detail')
                kwargs['breadcrumbs'] = breadcrumbs
                return kwargs

    """

    tag: str = "nav"
    aria_attributes: dict[str, str] = {"label": "breadcrumb"}  # type: ignore[misc]  # noqa: RUF012

    #: Apply this string of CSS classes to each breadcrumb title
    title_class: str | None = None
    #: The base set of breadcrumb items
    items: list[BreadcrumbItem] = []  # noqa: RUF012

    def __init__(self, *args, title_class: str | None = None, **kwargs):
        """
        Initialize a breadcrumb navigation component.

        Args:
            *args: Positional arguments passed to parent Block class
            title_class: CSS classes to apply to each breadcrumb title
            **kwargs: Additional keyword arguments passed to parent Block class

        """
        self.title_class = title_class if title_class else self.title_class
        super().__init__(*args, **kwargs)
        #: The list of :py:class:`BreadcrumbItem` objects from which we will
        #: build our breadcrumb HTML
        self.items = deepcopy(self.items)
        #: The ``<ol>`` that holds our breadcrumbs
        self.breadcrumbs = OrderedList(name="breadcrumb")
        self.add_block(self.breadcrumbs)

    def add_breadcrumb(self, title: str, url: str | None = None) -> None:
        """
        Add a new breadcrumb item to the breadcrumb trail.

        This method appends a new item to the end of the breadcrumb list.
        The last item added will be styled as the active/current item.

        Args:
            title: Display text for the breadcrumb
            url: Optional URL for the breadcrumb link. If None, the item will be
                displayed as plain text (typically for the current page).

        Examples:
            ... code-block:: python

                from wildewidgets import BreadcrumbBlock

                breadcrumbs = BreadcrumbBlock()
                breadcrumbs.add_breadcrumb('Home', url='/home')
                breadcrumbs.add_breadcrumb('Products', url='/products')
                breadcrumbs.add_breadcrumb('Product Detail')  # Current page has no URL

        """
        self.items.append(BreadcrumbItem(title=title, url=url))

    def get_context_data(self, *args, **kwargs) -> dict[str, Any]:
        """
        Prepare the context data for template rendering.

        This method builds the actual breadcrumb HTML elements from the stored
        breadcrumb items, adding the appropriate classes and marking the last
        item as active.

        Args:
            *args: Positional arguments passed to parent method
            **kwargs: Keyword arguments passed to parent method

        Returns:
            dict: Updated context dictionary with breadcrumb-specific data

        """
        for item in self.items:
            if self.title_class:
                title: Block = Block(item.title, tag="span", css_class=self.title_class)
            else:
                title = Block(item.title, tag="span")
            block = Link(title, url=item.url) if item.url else title
            self.breadcrumbs.add_block(block, name="breadcrumb-item")
        # Make the last li be active
        self.breadcrumbs.blocks[-1].add_class("active")  # type: ignore[union-attr]
        return super().get_context_data(*args, **kwargs)

    def flatten(self) -> str:
        """
        Convert all breadcrumb items to a single string.

        This method joins all breadcrumb titles with a separator, which is useful
        for creating page titles or meta descriptions that include the full
        navigation path.

        Returns:
            str: All breadcrumb titles joined with " - "

        Examples:
            ... code-block:: python

                from wildewidgets import BreadcrumbBlock

                breadcrumbs = BreadcrumbBlock()
                breadcrumbs.add_breadcrumb('Home')
                breadcrumbs.add_breadcrumb('Products')
                breadcrumbs.add_breadcrumb('Product Detail')
                print(breadcrumbs.flatten())
                # this will print: 'Home - Products - Product Detail'

        """
        return " - ".join([item.title for item in self.items])


class NavigationTogglerButton(Block):
    """
    A button that toggles responsive navigation components.

    This widget creates the familiar "hamburger" button that appears on mobile
    viewports to toggle the visibility of navigation menus. It's designed to work
    with Bootstrap's responsive navbar collapse behavior.

    Attributes:
        tag: HTML tag for the button ('button')
        block: CSS class for styling ('navbar-toggler')
        css_class: Additional CSS classes ('collapsed')
        attributes: HTML attributes for the button
        data_attributes: Data attributes for Bootstrap functionality
        aria_attributes: Accessibility attributes
        target: ID of the element to toggle (required)
        label: Accessibility label for the button

    Examples:
        ... code-block:: python

            from wildewidgets import NavigationTogglerButton

            toggler = NavigationTogglerButton(target='main-nav')

        This produces HTML similar to:

        .. code-block:: html

            <button type="button" class="navbar-toggler collapsed"
                    data-toggle="collapse" data-target="#main-nav"
                    aria-expanded="false" aria-controls="main-nav"
                    aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>

    """

    tag: str = "button"
    block: str = "navbar-toggler"
    css_class: str = "collapsed"
    attributes: dict[str, str] = {"type": "button"}  # type: ignore[misc]  # noqa: RUF012
    data_attributes: dict[str, str] = {"toggle": "collapse"}  # type: ignore[misc]  # noqa: RUF012
    aria_attributes: dict[str, str] = {"expanded": "false"}  # type: ignore[misc]  # noqa: RUF012

    #: The CSS id of the tag that this button toggles
    target: str | None = None
    #: The ARIA label for this button
    label: str = "Toggle navigation"

    def __init__(self, target: str | None = None, label: str | None = None, **kwargs):
        """
        Initialize a navigation toggler button.

        Args:
            target: CSS ID of the element to toggle (required)
            label: Accessibility label for the button (defaults to "Toggle navigation")
            **kwargs: Additional keyword arguments passed to parent Block class

        Raises:
            ValueError: If no target is provided

        """
        self.target = target if target else self.target
        self.label = label if label else self.label
        if not self.target:
            msg = (
                "No target supplied; define it either as a constructor kwarg or as "
                "a class attribute"
            )
            raise ValueError(msg)
        super().__init__(**kwargs)
        self._aria_attributes["label"] = self.label
        self._aria_attributes["controls"] = self.target
        self._data_attributes["target"] = f"#{self.target.lstrip('#')}"
        self.add_block(Block(tag="span", name="navbar-toggler-icon"))


class Navbar(Block):
    """
    A Bootstrap navbar component for site navigation.

    This class creates a horizontal Bootstrap navbar that can contain branding,
    menus, and other navigation elements. It handles responsive behavior and
    can be customized with different colors and breakpoints.

    Attributes:
        tag: HTML tag for the container ('aside')
        block: CSS class for styling ('navbar')
        VALID_BREAKPOINTS: Valid viewport sizes for responsive behavior
        VALID_BACKGROUND_COLORS: Valid background color options
        dark: Whether to use dark styling instead of light
        background_color: Optional background color
        contents_id: CSS ID for the menu container
        branding: Block to display as the navbar brand/logo
        contents: List of blocks to include in the navbar
        hide_below_viewport: Viewport size at which the menu collapses
        container_size: Width of the navbar container
        inner: Container block for navbar contents
        menu_container: Container for menu items that collapse on small screens

    Examples:
        With a subclass:

        ... code-block:: python
            from wildewidgets import Navbar, Menu, MenuItem, LinkedImage

            class MyMenu(Menu):
                items = [MenuItem(text='One', url='/one', icon='target')]

            class MyNavbar(Navbar):
                branding = LinkedImage(
                    src='/static/branding.png',
                    alt='My Brand',
                    url='#'
                )
                contents = [MyMenu()]

        With constructor arguments:

            ... code-block:: python

                from wildewidgets import Navbar, Menu, MenuItem, LinkedImage

                branding = LinkedImage(
                    src='/static/branding.png',
                    alt='My Brand',
                    url='#'
                )
                items = [MenuItem(text='One', url='/one'), ... ]
                menu = Menu(*items)
                sidebar = Navbar(menu, branding=branding)

        Adding menus later:

            ... code-block:: python

                from wildewidgets import Navbar, Menu, MenuItem

                items2 = [MenuItem(text='Foo', url='/foo'), ... ]
                menu2 = Menu(*items2)
                sidebar.add_to_menu_section(menu2)

    Args:
        *blocks: Blocks to add to the navbar
        contents_id: CSS ID for the menu container
        branding: Block to display as the navbar brand/logo
        hide_below_viewport: Viewport size at which the menu collapses
        container_size: Width of the navbar container
        dark: Whether to use dark styling
        background_color: Background color name
        **kwargs: Additional keyword arguments passed to parent Block class

    Raises:
        ValueError: If hide_below_viewport is not a valid breakpoint
        ValueError: If background_color is not a valid color

    """

    #: The HTML tag for the navbar container
    tag: str = "aside"
    #: The block name for the navbar, used for CSS styling
    block: str = "navbar"

    #: Valid values for ``navbar-expand-``. From
    #:`Navbar: How It Works <https://getbootstrap.com/docs/5.3/components/navbar/#how-it-works>`_
    VALID_BREAKPOINTS: Final[list[str]] = ["sm", "md", "lg", "xl", "xxl"]
    #: Valid background colors.  Note that these are Tabler colors, not Bootstrap
    #: colors.  We use Tabler colors because Tabler also defines an appropriate
    #: foreground color for each background color.
    VALID_BACKGROUND_COLORS: Final[list[str]] = [
        "blue",
        "azure",
        "indigo",
        "purple",
        "pink",
        "red",
        "orange",
        "yellow",
        "lime",
        "green",
        "teal",
        "cyan",
        "white",
    ]

    #: Set to ``True`` to use a dark background instead of light
    dark: bool = False
    #: If :py:attr:`dark` is ``True``, set the background color. Default: ``#1d273b``
    background_color: str | None = None
    #: the CSS id of the menu container.  Typically you won't need
    #: to change this unless you have namespace collisions with other CSS
    #: ids on your page.
    contents_id: str = "sidebar-menu"
    #: A block that will be displayed at the top of the container.
    #: A good choice might be a :py:class:`LinkedImage` or :py:class:`Image`
    branding: Block | None = None
    #: A list of blocks to include in our sidebar
    contents: list[Block] = []  # type: ignore[assignment]  # noqa: RUF012
    #: The viewport size at which our menu container collapses to be hidden,
    #: requiring the hamburger menu to show
    hide_below_viewport: str = "lg"
    #: The width of our actual navbar
    container_size: str = "fluid"

    def __init__(
        self,
        *blocks: Block,
        contents_id: str | None = None,
        branding: Block | None = None,
        hide_below_viewport: str | None = None,
        container_size: str | None = None,
        dark: bool | None = None,
        background_color: str | None = None,
        **kwargs,
    ):
        # TODO: why are we not using *blocks?  We say in the docstring that we
        # accept blocks, but we don't actually use them.  We should either use
        # them or remove the *blocks argument.
        self.contents = list(blocks) if blocks else self.contents
        # Set our attributes based on constructor arguments
        self.contents_id = contents_id if contents_id else self.contents_id
        self.hide_below_viewport = (
            hide_below_viewport if hide_below_viewport else self.hide_below_viewport
        )
        self.container_size = container_size if container_size else self.container_size
        self.dark = dark if dark is not None else self.dark
        self.background_color = (
            background_color if background_color is not None else self.background_color
        )
        if self.hide_below_viewport not in self.VALID_BREAKPOINTS:
            msg = (
                f'"{self.hide_below_viewport}" is not a valid breakpoint size. '
                f"Choose from: {', '.join(self.VALID_BREAKPOINTS)}"
            )
            raise ValueError(msg)
        if (
            self.background_color
            and self.background_color not in self.VALID_BACKGROUND_COLORS
        ):
            msg = (
                f'"{self.background_color}" is not a known color. '
                f"Choose from: {', '.join(self.VALID_BACKGROUND_COLORS)}"
            )
            raise ValueError(msg)

        super().__init__(**kwargs)
        # Set our hamburger menu breakpoint
        self.add_class(f"navbar-expand-{self.hide_below_viewport}")
        # light vs dark
        if self.dark:
            self.add_class("navbar-dark")
        # background color
        if self.background_color:
            self.add_class(f"bg-{self.background_color}")
            self.add_class(f"bg-{self.background_color}-fg")
        # Set our "role" attribute to make us more accessible
        self._attributes["role"] = "navigation"
        #: Everything inside our sidebar lives in this inner container
        margin_class = "ms-0" if self.container_size == "fluid" else "ms-auto"
        self.inner: Block = Container(size=self.container_size, css_class=margin_class)
        self.add_block(self.inner)
        #: This is the branding block at the start of the navbar
        self.branding: Block = branding if branding else deepcopy(self.branding)
        self.build_brand()
        # The menu toggler button for small viewports
        self.inner.add_block(NavigationTogglerButton(target=self.contents_id))
        #: This is the container for all menus
        self.menu_container: Block = CollapseWidget(
            css_id=self.contents_id, css_class="navbar-collapse"
        )
        self.inner.add_block(self.menu_container)
        for block in self.contents:
            self.add_to_menu_section(block)

    def add_blocks(self) -> None:
        """
        Override the parent method to do nothing.

        This method is intentionally empty to prevent blocks from being added
        directly to the navbar. Instead, blocks should be added to the menu
        section using add_to_menu_section().
        """

    def build_brand(self) -> None:
        """
        Build the navbar brand element.

        This method adds the brand/logo element to the navbar's inner container.
        It can be overridden in subclasses to customize branding behavior.
        """
        if self.branding:
            # Add the .navbar-brand class to our branding block to make it work
            # properly within the .navbar
            self.branding.add_class("navbar-brand")

    def add_to_menu_section(self, block: Block) -> None:
        """
        Add a block to the collapsible menu section of the navbar.

        This method should be used instead of add_block() to add navigation
        elements to the navbar. Items added this way will be part of the
        collapsible menu that toggles with the hamburger button on small screens.

        Args:
            block: The block to add to the menu section

        Example:
            ... code-block:: python

                from wildewidgets import Navbar, Menu, MenuItem

                navbar = Navbar()
                menu = Menu(MenuItem(text='Home', url='/'))
                navbar.add_to_menu_section(menu)

        """
        self.menu_container.add_block(block)

    def activate(self, text: str) -> bool:
        """
        Activate the menu item that matches the given text or URL.

        This method searches through all Menu blocks in the navbar and activates
        the first menu item that matches the provided text or URL.

        Args:
            text: The text or URL to match against menu items

        Returns:
            bool: True if a matching menu item was found and activated

        Example:
            ... code-block:: python

                from wildewidgets import Navbar, Menu, MenuItem

                navbar = Navbar()
                menu = Menu(MenuItem(text='Home', url='/'))
                navbar.add_to_menu_section(menu)
                navbar.activate('Home')

        """
        for block in self.menu_container.blocks:
            if isinstance(block, Menu):
                if block.activate(text):
                    return True
        return False


class TablerVerticalNavbar(Navbar):
    """
    A vertical navbar styled with Tabler design elements.

    This navbar variant is designed to be displayed as a sidebar with
    a vertical orientation. It has dark styling by default and provides
    consistent width options.

    Features:
    * Vertical orientation instead of horizontal
    * Dark mode by default
    * Fixed width (15rem or 18rem if wide=True)
    * Fixed position for scrolling pages
    * Includes open/close animations

    Attributes:
        block: CSS classes for styling
        dark: Always True for dark styling
        wide: If True, use wider 18rem layout instead of 15rem

    Examples:
        ... code-block:: python

            from wildewidgets import TablerVerticalNavbar, Menu, MenuItem, LinkedImage

            branding = LinkedImage(
                src='/static/branding.png',
                alt='My Brand',
                url='https://example.com',
                width='100%'
            )
            items = [MenuItem(text='Home', url='/home')]
            menu = Menu(*items)
            sidebar = TablerVerticalNavbar(menu, branding=branding)

    Args:
        *args: Positional arguments passed to parent Navbar class

    Keyword Args:
        wide: If True, use wider 18rem layout instead of 15rem
        **kwargs: Additional keyword arguments passed to parent Navbar class

    """

    block: str = "navbar navbar-vertical"
    dark: bool = True

    #: Make the navbar 18rem wide instead of 15rem
    wide: bool = False

    def __init__(self, *args, wide: bool | None = None, **kwargs):
        self.wide = wide if wide is not None else self.wide
        super().__init__(*args, **kwargs)
        if self.wide:
            self._css_class += " navbar-wide"

    def build_brand(self) -> None:
        """
        Build the navbar brand element with Tabler-specific styling.

        Overrides the parent method to wrap the branding in an h1 element
        with appropriate classes for Tabler design.
        """
        if self.branding:
            brand_container = Block(
                self.branding,
                tag="h1",
                css_class="navbar-brand navbar-brand-autodark flex-grow-1 "
                f"flex-{self.hide_below_viewport}-grow-0",
            )
            self.inner.add_block(brand_container)


class MenuHeading(Block):
    """
    A heading element for grouping menu items.

    This widget creates a styled heading within a Menu to separate groups of items.
    It's typically used for section titles in navigation menus.

    Attributes:
        block: CSS classes for styling
        css_class: Additional CSS classes for formatting
        text: The heading text to display

    Examples:
        .. code-block:: python

            from wildewidgets import MenuHeading

            heading = MenuHeading(text='Settings')

    Notes:
        This is often created automatically from MenuItem objects that have
        no URL and no children.

    Args:
        text: The heading text to display

    Keyword Args:
        **kwargs: Additional keyword arguments passed to parent Block class


    """

    block: str = "nav-link nav-subtitle"
    css_class: str = "nav-link my-1 fw-bold text-uppercase"

    #: The text of the heading
    text: str | None = None

    def __init__(self, text: str | None = None, **kwargs):
        self.text = text if text else self.text
        if not self.text:
            msg = '"text" is required as either a class attribute or keyword arg'
            raise ValueError(msg)
        super().__init__(**kwargs)
        self.add_block(self.text)


class NavItem(Block):
    """
    A navigation item for use in menus.

    This widget creates a list item with a link or heading, optionally with an icon.
    It represents a single navigation element in a menu or navbar.

    Attributes:
        tag: HTML tag for the container ('li')
        block: CSS class for styling ('nav-item')
        icon: Optional icon to display (string name or TablerMenuIcon)
        text: The text to display
        url: Optional URL to link to

    Examples:
        With keyword arguments:

            .. code-block:: python

                from wildewidgets import NavItem, TablerMenuIcon

                icon = TablerMenuIcon(icon='home')
                item = NavItem(text='Home', url='/', icon=icon)

        With a :py:class:`MenuItem`:

            .. code-block:: python

                from wildewidgets import NavItem, MenuItem

                menu_item = MenuItem(text='Home', url='/', icon='home')
                item = NavItem(item=menu_item)

        As a section heading:

            .. code-block:: python

                from wildewidgets import NavItem

                heading = NavItem(text='Settings')

    Keyword Args:
        text: The text to display
        icon: Optional icon to display (string name or TablerMenuIcon)
        url: Optional URL to link to
        active: Whether this item should be highlighted as active
        item: A MenuItem object to create this NavItem from
        **kwargs: Additional keyword arguments passed to parent Block class

    Raises:
        ValueError: If both item and other parameters are provided
        ValueError: If no text is provided

    """

    tag: str = "li"
    block: str = "nav-item"

    #: Either the name of a Bootstrap icon, or a :py:class:`TablerMenuIcon`
    #: object
    icon: str | TablerMenuIcon | None = None  # type: ignore[assignment]
    #: The text for the item.
    text: str | None = None
    #: The URL for the item.
    url: str | None = None

    def __init__(
        self,
        text: str | None = None,
        icon: str | TablerMenuIcon | None = None,
        url: str | None = None,
        active: bool = False,
        item: MenuItem | None = None,
        **kwargs,
    ):
        self.active: bool = active
        if item and (text or icon or url or active):
            msg = 'Specify "item" or ("text", "icon", "url", "active"), but not both'
            raise ValueError(msg)
        if item:
            self.text = item.text
            self.icon = item.icon if item.icon else deepcopy(self.icon)  # type: ignore[assignment]
            self.url = item.url if item.url else self.url
            self.active = item.active
        else:
            self.text = text if text else self.text
            self.icon = icon if icon else self.icon
            self.url = url if url else self.url
            if not self.text:
                msg = '"text" is required as either a class attribute or keyword arg'
                raise ValueError(msg)
        super().__init__(**kwargs)
        if self.active:
            self.add_class("active")
        icon_block: Block | None = None
        if self.icon:
            if isinstance(self.icon, TablerMenuIcon):
                icon_block = self.icon
            else:
                icon_block = TablerMenuIcon(icon=self.icon)
        contents: Block | None = None
        if self.url:
            contents = Link(url=self.url, css_class="nav-link")
            if icon_block:
                contents.add_block(icon_block)
            contents.add_block(self.text)
        else:
            contents = MenuHeading(text=self.text)
        self.add_block(contents)


# Submenus:


class ClickableNavDropdownControl(Block):
    """
    A control for dropdown menus with a separate clickable link.

    This specialized control provides both a clickable link and a dropdown toggle
    in one component. It allows the user to either navigate to a URL by clicking
    the main text, or open a dropdown menu by clicking a separate arrow.

    Attributes:
        block: CSS class for styling
        icon: Optional icon to display
        text: The text to display as the link
        url: The URL to navigate to when clicking the text
        link: The Link object for the clickable text
        control: The Link object that toggles the dropdown

    Examples:
        Basic usage:

            ... code-block:: python

                from wildewidgets import ClickableNavDropdownControl

                control = ClickableNavDropdownControl(
                    'dropdown-menu-id',
                    text='Products',
                    url='/products'
                )

        With an icon:

            ... code-block:: python

                from wildewidgets import ClickableNavDropdownControl

                control = ClickableNavDropdownControl(
                    'dropdown-menu-id',
                    text='Products',
                    url='/products',
                    icon='box'
                )
            )

    Args:
        menu_id: CSS ID of the dropdown menu to control

    Keyword Args:
        text: The text to display as the link
        icon: Optional icon to display
        url: The URL to navigate to when clicking the text
        active: Whether this item should be highlighted as active
        **kwargs: Additional keyword arguments passed to parent Block class

    Raises:
        ValueError: If no URL is provided
        ValueError: If no text is provided


    """

    block: str = "nav-item--clickable"

    #: Either the name of a Bootstrap icon, or a :py:class:`TablerMenuIcon`
    #: class or subclass
    icon: str | TablerMenuIcon | None = None  # type: ignore[assignment]
    #: The actual name of the dropdown
    text: str | None = None
    #: The URL to associated with the control
    url: str | None = None

    def __init__(
        self,
        menu_id: str,
        text: str | None = None,
        icon: str | TablerMenuIcon | None = None,
        url: str | None = None,
        active: bool = False,
        **kwargs,
    ):
        #: If this is ``True``, this control itself is active, but nothing
        #: in the related :py:class:`DropdownMenu` is
        self.active: bool = active
        self.text = text if text else self.text
        self.icon: str | TablerMenuIcon | None = icon if icon else deepcopy(self.icon)
        self.url = url if url else self.url
        if not self.url:
            msg = '"url" is required as either a class attribute of a keyword arg'
            raise ValueError(msg)
        if not self.text:
            msg = '"text" is required as either a class attribute of a keyword arg'
            raise ValueError(msg)
        super().__init__(**kwargs)
        # These classes make the link + control look right
        for klass in [
            "d-flex",
            "flex-row",
            "justify-content-between",
            "align-items-center",
        ]:
            self.add_class(klass)
        self.link = Link(url=self.url, name="nav-link")
        # make the clickable link
        if self.icon:
            if not isinstance(self.icon, TablerMenuIcon):
                self.link.add_block(TablerMenuIcon(icon=self.icon))
            else:
                self.link.add_block(self.icon)
        self.link.add_block(self.text)
        # make the actual dropdown control
        self.control = Link(
            css_class="nav-link dropdown-toggle",
            role="button",
            data_attributes={
                "toggle": "dropdown-ww",  # This data-bs-toggle is targeted by our own javascript  # noqa: E501
                "target": f"#{menu_id}",
            },
            aria_attributes={"expanded": "false"},
        )
        self.add_block(self.link)
        self.add_block(self.control)
        if self.active:
            self.add_class("active")

    def expand(self) -> None:
        """
        Set the dropdown to expanded state.

        This updates the aria-expanded attribute to 'true' to indicate
        that the associated dropdown menu is open.
        """
        self.control._aria_attributes["expanded"] = "true"

    def collapse(self) -> None:
        """
        Set the dropdown to collapsed state.

        This updates the aria-expanded attribute to 'false' to indicate
        that the associated dropdown menu is closed.
        """
        self.control._aria_attributes["expanded"] = "false"


class NavLinkToggle(Link):
    """
    A toggle control for collapsible content.

    This widget creates a link that toggles the visibility of a collapsible
    element. It includes styling for showing open/closed state and can
    optionally include an icon.

    Attributes:
        block: CSS class for styling
        name: Additional CSS class
        data_attributes: Data attributes for Bootstrap collapse functionality
        aria_attributes: Accessibility attributes
        icon: Optional icon to display
        text: The text to display
        collapse_id: CSS ID of the element to toggle

    Example:
        .. code-block:: python

            from wildewidgets import NavLinkToggle

            toggle = NavLinkToggle(
                text='Advanced Options',
                collapse_id='advanced-options'
            )

    Keyword Args:
        text: The text to display
        icon: Optional icon to display
        active: Whether this item should be highlighted as active
        collapse_id: CSS ID of the element to toggle
        **kwargs: Additional keyword arguments passed to parent Link class

    Raises:
        NavLinkToggle.RequiredAttrOrKwarg: If collapse_id is not provided
        NavLinkToggle.RequiredAttrOrKwarg: If text is not provided

    """

    block: str = "nav-link"
    name: str = "nav-link-toggle"
    data_attributes: dict[str, str] = {  # type: ignore[misc]  # noqa: RUF012
        "toggle": "collapse",
    }
    aria_attributes: dict[str, str] = {"expanded": "false"}  # type: ignore[misc]  # noqa: RUF012

    #: Either the name of a Bootstrap icon, or a :py:class:`TablerMenuIcon`
    #: class or subclass
    icon: str | TablerMenuIcon | None = None  # type: ignore[assignment]
    #: The title for the link
    text: str | None = None
    #: The CSS id of the Collapse that we control
    collapse_id: str | None = None

    def __init__(
        self,
        text: str | None = None,
        icon: str | TablerMenuIcon | None = None,
        active: bool = False,
        collapse_id: str | None = None,
        **kwargs,
    ):
        """
        Initialize a navigation link toggle.


        """
        #: This item is active, but nothing in the related :py:class:`DropdownMenu` is
        self.active: bool = active
        self.text = text if text else self.text
        self.icon = icon if icon else deepcopy(self.icon)
        self.collapse_id = collapse_id if collapse_id else self.collapse_id
        if self.collapse_id is None:
            msg = "collapse_id"
            raise self.RequiredAttrOrKwarg(msg)
        if not self.text:
            msg = "text"
            raise self.RequiredAttrOrKwarg(msg)
        super().__init__(role="button", **kwargs)
        self._data_attributes["target"] = self.collapse_id
        # these classes cause the up/down arrow to be nicely separated from the text
        self.add_class("d-flex")
        self.add_class("flex-row")
        self.add_class("justify-content-between")
        if self.icon:
            if isinstance(self.icon, TablerMenuIcon):
                icon_block = self.icon
            else:
                icon_block = TablerMenuIcon(icon=self.icon)
            self.add_block(icon_block)
        self.add_block(self.text)
        if self.active:
            self.add_class("active")

    def expand(self) -> None:
        """
        Set the toggle to expanded state.

        This updates the aria-expanded attribute to 'true' to indicate
        that the associated collapsible element is open.
        """
        self._aria_attributes["expanded"] = "true"

    def collapse(self) -> None:
        """
        Set the toggle to collapsed state.

        This updates the aria-expanded attribute to 'false' to indicate
        that the associated collapsible element is closed.
        """
        self._aria_attributes["expanded"] = "false"


class NavDropdownControl(Link):
    """
    A control button for dropdown menus.

    This widget creates a link that toggles the visibility of a dropdown menu.
    It can include an optional icon and handles the open/closed state.

    Attributes:
        block: CSS class for styling
        name: Additional CSS class
        data_attributes: Data attributes for Bootstrap dropdown functionality
        aria_attributes: Accessibility attributes
        icon: Optional icon to display
        text: The text to display
        button_id: CSS ID of this button (required for connecting to dropdown)

    Examples:
        ... code-block:: python

            from wildewidgets import NavDropdownControl

            control = NavDropdownControl(
                text='Options',
                button_id='options-dropdown'
            )

            control = NavDropdownControl(
                text='Options',
                icon='gear',
                button_id='options-dropdown'
            )

    Args:
        text: The text to display
        icon: Optional icon to display
        active: Whether this item should be highlighted as active
        button_id: CSS ID for this button (required)
        **kwargs: Additional keyword arguments passed to parent Link class

    Raises:
        NavDropdownControl.RequiredAttrOrKwarg: If text is not provided
        NavDropdownControl.RequiredAttrOrKwarg: If button_id is not provided

    """

    block: str = "nav-link"
    name: str = "dropdown-toggle"
    data_attributes: dict[str, str] = {"toggle": "dropdown", "auto-close": "true"}  # type: ignore[misc]  # noqa: RUF012
    aria_attributes: dict[str, str] = {"expanded": "false"}  # type: ignore[misc]  # noqa: RUF012
    #: Either the name of a Bootstrap icon, or a :py:class:`TablerMenuIcon`
    #: class or subclass
    icon: str | TablerMenuIcon | None = None  # type: ignore[assignment]
    #: The actual name of the dropdown
    text: str | None = None
    #: The CSS Id to assign to this button.  We need this to tie the
    #: button to the actual :py:class:`DropdownItem`
    button_id: str | None = None

    def __init__(
        self,
        text: str | None = None,
        icon: str | TablerMenuIcon | None = None,
        active: bool = False,
        button_id: str | None = None,
        **kwargs,
    ):
        #: This item is active, but nothing in the related :py:class:`DropdownMenu` is
        self.active: bool = active
        self.text = text if text else self.text
        self.icon = icon if icon else deepcopy(self.icon)
        self.button_id = button_id if button_id else self.button_id
        if not self.text:
            msg = "text"
            raise self.RequiredAttrOrKwarg(msg)
        if not self.button_id:
            msg = "button_id"
            raise self.RequiredAttrOrKwarg(msg)
        super().__init__(css_id=self.button_id, role="button", **kwargs)
        if self.icon:
            if isinstance(self.icon, TablerMenuIcon):
                icon_block = self.icon
            else:
                icon_block = TablerMenuIcon(icon=self.icon)
            self.add_block(icon_block)
        self.add_block(self.text)
        if self.active:
            self.add_class("active")

    def expand(self) -> None:
        """
        Set the dropdown to expanded state.

        This updates the aria-expanded attribute to 'true' to indicate
        that the associated dropdown menu is open.
        """
        self._aria_attributes["expanded"] = "true"

    def collapse(self) -> None:
        """
        Set the dropdown to collapsed state.

        This updates the aria-expanded attribute to 'false' to indicate
        that the associated dropdown menu is closed.
        """
        self._aria_attributes["expanded"] = "false"


class DropdownItem(Link):
    """
    An item within a dropdown menu.

    This widget creates a link styled for use within dropdown menus.
    It can include an optional icon and handles active state.

    Attributes:
        block: CSS class for styling
        icon: Optional icon to display
        text: The text to display

    Examples:
        With no icon:

        .. code-block:: python

            from wildewidgets import DropdownItem

            item = DropdownItem(
                text='Edit Profile',
                url='/profile/edit'
            )

        With an icon:

            ... code-block:: python

                from wildewidgets import DropdownItem

                item = DropdownItem(
                    text='Settings',
                    url='/settings',
                    icon='gear'
                )

    Keyword Args:
        text: The text to display
        icon: Optional icon to display
        active: Whether this item should be highlighted as active
        item: A MenuItem object to create this DropdownItem from
        **kwargs: Additional keyword arguments passed to parent Link class

    Raises:
        ValueError: If both item and other parameters are provided
        ValueError: If no text is provided
        ValueError: If no URL is provided

    """

    block: str = "dropdown-item"

    #: this is either the name of a bootstrap icon, or a :py:class:`TablerMenuIcon`
    #: class or subclass
    icon: str | TablerMenuIcon | None = None  # type: ignore[assignment]
    #: The text for the item.
    text: str | None = None

    def __init__(
        self,
        text: str | None = None,
        icon: str | None = None,
        active: bool = False,
        item: MenuItem | None = None,
        **kwargs,
    ):
        # Does this item represent the page we're on?
        self.active: bool = active
        if item and (text or icon or kwargs.get("url")):
            msg = 'Specify "item" or ("text", "icon", "url"), but not both'
            raise ValueError(msg)
        if item:
            self.text = item.text
            self.icon = item.icon if item.icon else self.icon  # type: ignore[assignment]
            if item.url:
                kwargs["url"] = item.url
            self.active = item.active
        else:
            self.text = text if text else self.text
            self.icon = icon if icon else self.icon
        if not self.text:
            msg = '"text" is required as either a class attribute or keyword arg'
            raise ValueError(msg)
        if not self.url:
            msg = '"url" is required as either a class attribute or keyword arg'
            raise ValueError(msg)
        super().__init__(**kwargs)
        if self.active:
            self.add_class("active")
        icon_block: Block | None = None
        if self.icon:
            icon_block = TablerMenuIcon(icon=self.icon, css_class="text-white")  # type: ignore[arg-type]
        if icon_block:
            self.add_block(icon_block)
        self.add_block(self.text)


class DropdownMenu(Block):
    """
    A `Tabler dropdown menu <https://preview.tabler.io/docs/dropdowns.html>`_.

    Typically, you won't use this directly, but instead it will be created for
    you from a :py:class:`MenuItem` specification when :py:attr:`MenuItem.url`
    is not ``None``.

    Examples:
        ... code-block:: python

            from wildewidgets import DropdownMenu, MenuItem, NavDropdownControl

            items = [
                MenuItem(text='One', url='/one', icon='1-circle'),
                MenuItem(text='Two', url='/two', icon='2-circle'),
                MenuItem(text='Three', url='/three', icon='3-circle'),
            ]
            button = NavDropdownControl(
                text='My Dropdown Menu',
                icon='arrow-down-square-fill',
                button_id='my-button'
            )
            menu = DropdownMenu(*items, button_id=button.button_id)

    Args:
        *items: the list of :py:class:`MenuItem` objects to insert into
            this menu

    Keyword Args:
        button_id: it CSS id for the button

    Raises:
        ValueError: one or more of the settings failed validation

    """

    block: str = "dropdown-menu"

    #: A list of :py:class:`MenuItem` objects to add to this dropdown menu
    items: Iterable[MenuItem] = []
    #: The id of the dropdown-toggle button that controls this menu
    button_id: str | None = None

    def __init__(self, *items: MenuItem, button_id: str | None = None, **kwargs):
        self.button_id = button_id if button_id else self.button_id
        if items:
            self.items: Iterable[MenuItem] = items
        else:
            self.items = deepcopy(self.items)
        super().__init__(**kwargs)
        if not self.button_id and not self._css_id:
            msg = (
                'Either "button_id" or "css_id" are required as either class '
                "attributes or keyword args"
            )
            raise ValueError(msg)
        if self.button_id:
            self._aria_attributes["labelledby"] = self.button_id
        for item in items:
            self.add_item(item=item)

    def add_item(
        self,
        text: str | None = None,
        url: str | None = None,
        icon: str | TablerMenuIcon | None = None,
        active: bool = False,
        item: MenuItem | None = None,
    ) -> None:
        """
        Add a new item to this :py:class:`DropdownMenu`.

        Keyword Args:
            icon: Either the name of a Bootstrap icon, or a
                :py:class:`TablerMenuIcon` object
            text: The text for the item
            url: The URL for the item
            active: ``True`` if this represents the page we're currently on
            item: a :py:class:`MenuItem`

        Raises:
            ValueError: one or more of the settings failed validation

        """
        if item and (text or icon or url or active):
            msg = 'Specify "item" or ("text", "icon", "url"), but not both'
            raise ValueError(msg)
        if not item:
            if not text:
                msg = '"text" is required if "item" is not provided'
                raise ValueError(msg)
            item = MenuItem(text=text, url=url, icon=icon, active=active)
        if item.items:
            self.add_block(
                NavDropdownItem(
                    *item.items,
                    text=item.text,
                    url=item.url,
                    icon=item.icon,  # type: ignore[arg-type]
                )
            )
        else:
            self.add_block(DropdownItem(item=item))

    def show(self) -> None:
        """
        Force this dropdown menu to be shown.
        """
        self.add_class("show")

    def hide(self) -> None:
        """
        Force this dropdown menu to be hidden.
        """
        self.remove_class("show")


class NavDropdownItem(Block):
    """
    An item in a :py:class:`Menu` that opens a dropdown submenu.

    Typically, you won't use this directly, but instead it will be created for
    you from a :py:class:`MenuItem` specification when :py:attr:`MenuItem.items`
    is not empty.

    Example:
        ... code-block:: python

            from wildewidgets import Menu, MenuItem, NavDropdownItem

            sub_items = [
                MenuItem(text='One', url='/one', icon='1-circle'),
                MenuItem(text='Two', url='/two', icon='2-circle'),
                MenuItem(text='Three', url='/three', icon='3-circle'),
            ]
            item = NavDropdownItem(*sub_items, text='My Submenu', icon='target')
            menu = Menu(item)

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

    tag: str = "li"
    block: str = "nav-item dropdown"

    #: this is either the name of a bootstrap icon, or a :py:class:`TablerMenuIcon`
    #: class or subclass
    icon: str | TablerMenuIcon | None = None  # type: ignore[assignment]
    #: The actual name of the dropdown
    text: str | None = None
    #: The URL for the control text.  Use this if you want :py:attr:`text` to be
    #: clickable separately from opening the dropdown menu
    url: str | None = None
    #: The list of items in this dropdown menu
    items: Iterable[MenuItem] = []

    def __init__(
        self,
        *items: MenuItem,
        text: str | None = None,
        icon: str | TablerMenuIcon | None = None,
        url: str | None = None,
        active: bool = False,
        **kwargs,
    ):
        #: The control for opening the dropdown menu is active, but nothing in the
        #: related :py:class:`DropdownMenu` is active
        self.active = active
        #: The control that opens and closes :py:attr:`menu`
        self.control: NavDropdownControl | ClickableNavDropdownControl
        #: The :py:class:`DropdownMenu`  that :py:attr:`control` opens
        self.menu: DropdownMenu
        self.text = text if text else self.text
        self.url = url if url else self.url
        self.icon = icon if icon else deepcopy(self.icon)
        if not self.text:
            msg = '"text" is required as either a class attribute of a keyword arg'
            raise ValueError(msg)
        if items:
            self.items: Iterable[MenuItem] = items
        else:
            self.items = deepcopy(self.items)
        super().__init__(**kwargs)
        if self.url:
            # We need to be able to click on the control to get to a page
            menu_id: str = f"nav-menu-{self.text.lower()}"
            menu_id = re.sub("[ ._]", "-", menu_id)
            self.menu = DropdownMenu(*self.items, css_id=menu_id)
            self.control = ClickableNavDropdownControl(
                menu_id=menu_id,
                text=self.text,
                icon=self.icon,
                url=self.url,
                active=self.active,
            )
            # TODO: should we set up aria-labelledby on the menu to point to the
            # control?
        else:
            # We don't need to be able to click on the control to get to a page
            button_id: str = f"nav-item-{self.text.lower()}"
            button_id = re.sub("[ ._]", "-", button_id)
            self.control = NavDropdownControl(
                button_id=button_id, text=self.text, icon=self.icon, active=self.active
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

    def get_context_data(self, **kwargs) -> dict[str, Any]:
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
        Subclassing:

            .. code-block:: python

                from wildewidgets import Menu, MenuItem

                class MyMenu(Menu):

                    items = [
                        MenuItem(text='One', url='/one', icon='1-circle'),
                        MenuItem(text='Two', url='/two', icon='2-circle'),
                        MenuItem(text='Three', url='/three', icon='3-circle'),
                    ]

        Constructor:

            .. code-block:: python

                from wildewidgets import Menu, MenuItem

                menu = Menu(
                    MenuItem(text='One', url='/one', icon='1-circle'),
                    MenuItem(text='Two', url='/two', icon='2-circle'),
                    MenuItem(text='Three', url='/three', icon='3-circle'),
                )

        ``Menu.add_item``:

            .. code-block:: python

                from wildewidgets import Menu, MenuItem

                menu = Menu()
                menu.add_item(MenuItem(text='One', url='/one', icon='1-circle'))
                menu.add_item(MenuItem(text='Two', url='/two', icon='2-circle'))
                menu.add_item(MenuItem(text='Three', url='/three', icon='3-circle'))

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

    tag: str = "div"
    block: str = "menu"
    css_class: str = "me-1"

    #: The list of items in this menu
    items: Iterable[MenuItem] = []
    #: The title for this menu
    title: str | None = None
    #: The HTML tag for this title
    title_tag: str = "h4"
    #: CSS classes to apply to the title
    title_css_classes: str = ""

    def __init__(
        self,
        *items: MenuItem,
        title: str | None = None,
        title_tag: str | None = None,
        title_css_classes: str | None = None,
        **kwargs,
    ):
        self.title = title if title else self.title
        self.title_tag = title_tag if title_tag else self.title_tag
        self.title_css_classes = (
            title_css_classes if title_css_classes else self.title_css_classes
        )
        if items:
            self._items: list[MenuItem] = list(items)
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
        ul = Block(tag="ul", css_class="navbar-nav")
        if self.title:
            self.add_block(
                Block(
                    self.title,
                    tag=self.title_tag,
                    css_class=self.title_css_classes + " menu-title",
                )
            )
        self.add_block(ul)
        for item in items:
            if item.items:
                ul.add_block(
                    NavDropdownItem(
                        *item.items,
                        text=item.text,
                        icon=item.icon,  # type: ignore[arg-type]
                        url=item.url,
                        active=item.active,
                    )
                )
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
        Activate the menu item matching the given text or URL.

        This method searches through all menu items (including nested items in
        dropdowns) and sets the first matching item to active. This is useful
        for highlighting the current page in the navigation.

        Args:
            text: Text or URL to match against menu items

        Returns:
            bool: True if a matching item was found and activated

        Examples:
            >>> menu = Menu(
            ...     MenuItem(text='Home', url='/'),
            ...     MenuItem(text='Products', url='/products/')
            ... )
            >>> menu.activate('/products/')  # Activate by URL
            True
            >>> menu.activate('Home')  # Activate by text
            True

        """
        return any(item.set_active(text) for item in self._items)


# ==============================
# View mixins
# ==============================


class NavbarMixin:
    """
    A mixin for Django class-based views to manage navigation components.

    This mixin provides a standardized way to integrate navigation components
    (like navbars and submenus) into Django views. It adds navbar instances to
    the template context and handles the activation of menu items based on the
    current page.

    To use this mixin:
    1. Define your Navbar classes
    2. Subclass this mixin in your views
    3. Set the navbar_class and menu_item attributes
    4. In your template, render the "menu" and "submenu" context variables

    Attributes:
        navbar_class: The Navbar subclass to use as primary navigation
        menu_item: Text or URL of the item to mark as active in the primary navbar
        secondary_navbar_class: Optional Navbar subclass for secondary navigation
        secondary_menu_item: Text or URL of the item to mark as active in the
            secondary navbar

    Examples:
        Creating a view with navigation:

        .. code-block:: python

            class MainNavbar(Navbar):
                # Navbar definition...

            class ProjectsView(NavbarMixin, ListView):
                navbar_class = MainNavbar
                menu_item = 'Projects'  # Will highlight "Projects" in the menu

                def get_queryset(self):
                    # View implementation...

        In your template:

        .. code-block:: html

            {% wildewidgets menu %}
            <div class="container">
                <!-- Your page content -->
            </div>

    """

    #: The :py:class:`Navbar`` subclass that acts as our primary navigation
    navbar_class: type[Navbar] = Navbar
    #: The text or URL of an item in one of our :py:attr:`navbar_class` menus to
    #: set active
    menu_item: str | None = None
    #: The :py:class:`Navbar` subclass that holds our secondary menus
    secondary_navbar_class: type[Navbar] | None = None
    #: The text or URL of an item in one of our
    #: :py:attr:`secondary_navbar_class` menus to set active
    secondary_menu_item: str | None = None

    def get_navbar_class(self) -> type[Navbar]:
        """
        Return the :py:class:`Navbar` subclass for the main menu.  Overriding
        this will allow you to programmatically determine your at view time.

        Returns:
            The class of the :py:class:`Navbar` subclass to use for our
            main menu.

        """
        return self.navbar_class

    def get_menu_item(self) -> str | None:
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
        Create and return an instance of the primary navbar.

        This method instantiates the navbar_class and returns it. Override this
        method if you need custom initialization of your navbar.

        Returns:
            Navbar: An instance of the primary navbar class

        Raises:
            ImproperlyConfigured: If navbar_class is None

        """
        navbar_class = self.get_navbar_class()
        if not navbar_class:
            msg = '"navbar_class" must not be None'
            raise ImproperlyConfigured(msg)
        return navbar_class()

    def get_secondary_navbar_class(self) -> type[Navbar] | None:
        """
        Return our :py:class:`Navbar` subclass for the secondary navbar.

        Returns:
            The class of the :py:class:`Navbar` subclass to use for our
            secondary navbar, if any.

        """
        return self.secondary_navbar_class

    def get_secondary_menu_item(self) -> str | None:
        """
        Return the text of an item to set active in our secondary menu
        """
        return self.secondary_menu_item

    def get_secondary_navbar(self) -> Navbar | None:
        """
        Instantiate and return our :py:class:`Navbar` subclass for our
        secondary navbar.

        Returns:
            The instantiated :py:class:`Navbar` subclass instance to use for our
            secondary menu, if any.

        """
        secondary_navbar_class = self.get_secondary_navbar_class()
        if secondary_navbar_class:
            return secondary_navbar_class()
        return None

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """
        Add navigation components to the template context.

        This method:
        1. Creates the primary navbar and adds it as 'menu'
        2. Activates the appropriate menu item
        3. If applicable, creates the secondary navbar and adds it as 'submenu'
        4. Activates the appropriate secondary menu item

        Returns:
            Dict[str, Any]: The updated context dictionary

        """
        kwargs["menu"] = self.get_navbar()
        if menu_item := self.get_menu_item():
            kwargs["menu"].activate(menu_item)
        secondary_navbar = self.get_secondary_navbar()
        if secondary_navbar:
            kwargs["submenu"] = secondary_navbar
            if submenu_item := self.get_secondary_menu_item():
                secondary_navbar.activate(submenu_item)
        return super().get_context_data(**kwargs)  # type: ignore[misc]
