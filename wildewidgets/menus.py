from __future__ import annotations

import random
from typing import Any, ClassVar

from django import template
from django.urls import reverse

from wildewidgets.views import WidgetInitKwargsMixin


class BasicMenu(WidgetInitKwargsMixin):
    """
    Basic menu widget.

    A basic menu requires only one class attribute defined, :py:attr:`items`.

    Example:
        .. code-block:: python

            from wildewidgets import BasicMenu

            class MainMenu(BasicMenu):
                items = [
                    ('Users', 'core:home'),
                    ('Uploads','core:uploads'),
                ]

    """

    #: The Django template file to use for rendering the menu.
    template_file: str = "wildewidgets/menu.html"
    #: The CSS classes to use for the navbar.  This can be set to
    navbar_classes: str = "navbar-expand-lg navbar-light"
    #: The CSS class to use for the container that holds the navbar.
    container: str = "container-lg"
    #: The image to use for the brand logo.  If this is set, the brand text will
    #: not be displayed.  If you want to use a brand text, set this to
    #: ``None``.  The image should be a URL or a static file path.
    brand_image: str | None = None
    #: The CSS width to use for the brand image.  This is only used if
    #: :py:attr:`brand_image` is set.  If you want the image to be responsive,
    #: set this to ``100%``.
    brand_image_width: str = "100%"
    #: The text to use for the brand.
    brand_text: str | None = None
    #: The URL to use for the brand link.  If this is set, the brand image or
    #: text will be used as the link.
    brand_url: str = "#"
    #: A list of tuples that define the items to list in the menu, where the
    #: first element is the menu item text and the second element is the URL
    #: name.  A third optional element in the tuple can be a dictionary of get
    #: arguments
    items: ClassVar[
        list[tuple[str, str | list[tuple[str, str | None]] | dict[str, str] | None]]
    ] = []

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ARG002
        self.menu: dict[str, Any] = {}
        self.active: str | None = None
        if args:
            self.active_hierarchy: list[str] = args[0].split("/")
        else:
            self.active_hierarchy = []

    def build_menu(self) -> None:
        """
        Build the menu structure based on the active hierarchy.

        This method processes the items defined in the class attribute and creates
        a structured representation of the menu. It handles both regular menu items
        and submenus, and marks the appropriate items as active based on the
        active_hierarchy.

        The method:

        1. Processes each item in the items list
        2. Creates appropriate data structures for regular items and submenus
        3. Marks items as active if they match the active_hierarchy
        4. Adds query parameters if specified in the item definition

        Note:
            This method is called automatically by get_content() and doesn't need
            to be called directly.

        """
        if len(self.active_hierarchy) > 0:
            for item in self.items:
                data: dict[str, Any] = {}
                if isinstance(item[1], str):
                    data["url"] = reverse(item[1])
                    data["extra"] = ""
                    data["kind"] = "item"

                    if len(item) > 2 and item[2] is not None:  # noqa: PLR2004
                        extra = item[2]
                        if isinstance(extra, dict):
                            extra_list = []
                            for k, v in extra.items():
                                extra_list.append(f"{k}={v}")
                            extra_str = f"?{'&'.join(extra_list)}"
                            data["extra"] = extra_str
                elif isinstance(item[1], list):
                    if len(self.active_hierarchy) > 1:
                        submenu_active = self.active_hierarchy[1]
                    else:
                        submenu_active = None
                    data = self.parse_submemu(item[1], submenu_active)

                self.add_menu_item(item[0], data, item[0] == self.active_hierarchy[0])

    def add_menu_item(
        self, title: str, data: dict[str, Any], active: bool = False
    ) -> None:
        """
        Add a menu item to the menu structure.

        This method adds a new item to the menu with the specified title and data,
        and optionally marks it as the active item.

        Args:
            title: The text to display for the menu item
            data: Dictionary containing the item's configuration (url, kind, etc.)

        Keyword Args:
            active: Whether this item should be marked as active

        """
        self.menu[title] = data
        if active:
            self.active = title

    def parse_submemu(
        self, items: list[tuple[str, str | None]], submenu_active: str | None
    ) -> dict[str, Any]:
        """
        Parse and create a submenu structure.

        This method processes a list of submenu items and creates a structured
        representation of the submenu. It handles regular items and dividers,
        and marks the appropriate item as active based on the submenu_active parameter.

        Args:
            items: List of tuples defining submenu items (title, url, [extra])

        Keyword Args:
            submenu_active: The name of the submenu item to mark as active

        Returns:
            dict: A dictionary containing the structured submenu data

        """
        data: dict[str, Any] = {"kind": "submenu"}
        sub_menu_items: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, tuple):
                continue
            if item[0] == "divider":
                subdata: dict[str, Any] = {"divider": True}
            else:
                subdata = {
                    "title": item[0],
                    "url": reverse(item[1]) if item[1] else "#",
                    "extra": "",
                    "divider": False,
                    "active": item[0] == submenu_active,
                }

            if len(item) > 2:  # noqa: PLR2004
                subdata["extra"] = self.convert_extra(item[2])
            sub_menu_items.append(subdata)

        data["items"] = sub_menu_items
        return data

    def get_content(self, **kwargs: Any) -> str:  # noqa: ARG002
        """
        Render the menu as HTML content.

        This method:

        1. Builds the menu structure
        2. Creates a context dictionary with all necessary data
        3. Renders the template with the context

        Keyword Args:
            **kwargs: Additional arguments (unused)

        Returns:
            str: The rendered HTML content for the menu

        """
        self.build_menu()
        context = {
            "menu": self.menu,
            "active": self.active,
            "navbar_classes": self.navbar_classes,
            "navbar_container": self.container,
            "brand_image": self.brand_image,
            "brand_image_width": self.brand_image_width,
            "brand_text": self.brand_text,
            "brand_url": self.brand_url,
            "vertical": "navbar-vertical" in self.navbar_classes,
            "target": random.randrange(0, 10000),  # noqa: S311
        }
        html_template = template.loader.get_template(self.template_file)
        return html_template.render(context)

    def __str__(self) -> str:
        """
        Return the string representation of the menu.

        This method allows the menu to be used directly in templates via the
        {{ menu }} syntax.

        Returns:
            str: The rendered HTML content for the menu

        """
        return self.get_content()


class DarkMenu(BasicMenu):
    """
    A dark-themed navigation menu.

    This class extends the BasicMenu with dark styling using Bootstrap's dark
    navbar classes.  It provides a dark background with light text, suitable for
    applications with darker themes.

    Attributes:
        navbar_classes: Bootstrap classes for styling the navbar with dark theme

    Example:
        .. code-block:: python

            from wildewidgets import DarkMenu

            class MainDarkMenu(DarkMenu):
                items = [
                    ('Dashboard', 'dashboard'),
                    ('Reports', 'reports'),
                ]

    """

    navbar_classes = "navbar-expand-lg navbar-dark bg-secondary"


class VerticalDarkMenu(BasicMenu):
    """
    A vertical dark-themed navigation menu.

    This class extends the BasicMenu with dark styling and vertical orientation.
    It's particularly useful for sidebar navigation in applications with darker
    themes.

    Attributes:
        navbar_classes: Bootstrap classes for styling a vertical dark navbar

    Example:
        .. code-block:: python

            from wildewidgets import VerticalDarkMenu

            class SidebarMenu(VerticalDarkMenu):
                items = [
                    ('Profile', 'user_profile'),
                    ('Settings', 'user_settings'),
                    ('Logout', 'logout'),
                ]

    """

    navbar_classes = "navbar-vertical navbar-expand-lg navbar-dark"


class LightMenu(BasicMenu):
    """
    A light-themed navigation menu.

    This class extends the BasicMenu with light styling, which is also the
    default for BasicMenu.  It provides a light background with dark text,
    suitable for standard application layouts.

    Attributes:
        navbar_classes: Bootstrap classes for styling the navbar with light theme

    Example:
        .. code-block:: python

            from wildewidgets import LightMenu

            class MainLightMenu(LightMenu):
                items = [
                    ('Home', 'home'),
                    ('About', 'about'),
                    ('Contact', 'contact'),
                ]

    """

    navbar_classes = "navbar-expand-lg navbar-light"


class MenuMixin:
    """
    A mixin for adding menu support to Django class-based views.

    This mixin provides methods for including primary and secondary navigation menus
    in Django views. It automatically adds menu instances to the template context,
    making it easy to integrate navigation in templates.

    To use this mixin:

    1. Define menu classes by subclassing :py:class:`BasicMenu` or its variants
    2. Add this mixin to your view classes
    3. Set class attributes to specify which menus to use and which items to activate

    You must define the :py:attr:`menu_class` and the :py:attr:`menu_item`, but
    :py:attr:`submenu_class` and the :py:attr:`submenu_item` are optional. If
    you do not set them, no secondary menu will be displayed.

    Example:
        With no secondary menu:

        .. code-block:: python

            from django.views.generic import TemplateView
            from wildewidgets import BasicMenu, MenuMixin

            class MainMenu(BasicMenu):
                items = [
                    ('Home', 'home'),
                    ('About', 'about'),
                    ('Contact', 'contact'),
                ]

            class DashboardView(MenuMixin, TemplateView):
                template_name = "dashboard.html"
                menu_class = MainMenu
                menu_item = "Home"

        With a secondary menu:

        .. code-block:: python

            from django.views.generic import TemplateView
            from wildewidgets import BasicMenu, LightMenu, MenuMixin

            class MainMenu(BasicMenu):
                items = [
                    ('Home', 'home'),
                    ('About', 'about'),
                    ('Contact', 'contact'),
                ]

            class DashboardSubmenu(LightMenu):
                items = [
                    ('Overview', 'dashboard:overview'),
                    ('Statistics', 'dashboard:statistics'),
                    ('Settings', 'dashboard:settings'),
                ]

            class DashboardView(MenuMixin, TemplateView):
                template_name = "dashboard.html"
                menu_class = MainMenu
                menu_item = "Home"
                submenu_class = DashboardSubmenu
                submenu_item = "Overview"

    """

    #: The primary menu class to use for the view.
    #: This should be a subclass of BasicMenu or one of its variants.
    #: If set to None, no primary menu will be displayed.
    menu_class: type[BasicMenu] | None = None
    #: The active item for the primary menu.
    menu_item: str | None = None
    #: The secondary menu class to use for the view.
    submenu_class: type[BasicMenu] | None = None
    #: The active item for the secondary menu.
    submenu_item: str | None = None

    def get_menu_class(self) -> type[BasicMenu] | None:
        """
        Get the class to use for the primary menu.

        This method returns the menu_class attribute by default, but can be
        overridden to provide dynamic menu class selection.

        Returns:
            The menu class to use, or None if no menu should be displayed

        """
        return self.menu_class

    def get_menu_item(self) -> str | None:
        """
        Get the active item for the primary menu.

        This method returns the menu_item attribute by default, but can be
        overridden to provide dynamic active item selection.

        Returns:
            The name of the menu item to mark as active, or None if no item
            should be active

        """
        return self.menu_item

    def get_menu(self) -> BasicMenu | None:
        """
        Get an instance of the primary menu.

        This method instantiates the menu class with the active item.

        Returns:
            An instance of the menu, or None if no menu class is specified

        """
        menu_class = self.get_menu_class()
        if menu_class:
            menu_item = self.get_menu_item()
            return menu_class(menu_item)  # pylint: disable=not-callable
        return None

    def get_submenu_class(self) -> type[BasicMenu] | None:
        """
        Get the class to use for the secondary menu.

        This method returns the submenu_class attribute by default, but can be
        overridden to provide dynamic submenu class selection.

        Returns:
            The submenu class to use, or None if no submenu should be displayed

        """
        return self.submenu_class

    def get_submenu_item(self) -> str | None:
        """
        Get the active item for the secondary menu.

        This method returns the submenu_item attribute by default, but can be
        overridden to provide dynamic active item selection.

        Returns:
            The name of the submenu item to mark as active, or None if no item
            should be active

        """
        return self.submenu_item

    def get_submenu(self) -> BasicMenu | None:
        """
        Get an instance of the secondary menu.

        This method instantiates the submenu class with the active item.

        Returns:
            An instance of the submenu, or None if no submenu class is specified

        """
        submenu_class = self.get_submenu_class()
        if submenu_class:
            submenu_item = self.get_submenu_item()
            return submenu_class(submenu_item)  # pylint: disable=not-callable
        return None

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Add menu instances to the template context.

        This method adds the primary and secondary menu instances to the context
        if they are available.

        Args:
            **kwargs: Additional context variables

        Returns:
            The updated template context with menu instances

        """
        menu = self.get_menu()
        submenu = self.get_submenu()
        if menu:
            kwargs["menu"] = menu
        if submenu:
            kwargs["submenu"] = submenu
        return super().get_context_data(**kwargs)  # type: ignore[misc]
