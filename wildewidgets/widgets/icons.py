from __future__ import annotations

from typing import Any

from django.core.exceptions import ImproperlyConfigured

from .base import Block


class FontIcon(Block):
    """
    Render a font-based Bootstrap icon, for example:

    .. code-block:: html

        <i class="bi-star"></i>

    See the `Boostrap Icons <https://icons.getbootstrap.com/>`_ list for the
    list of icons.  Find an icon you like, and use the name of that icon on that
    page as the ``icon`` kwarg to the constructor, or set it as the :py:attr:`icon`
    class variable.

    Example:
        .. code-block:: python

            from wildewidgets import FontIcon

            icon = FontIcon(icon="star")

    Keyword Args:
        icon: the name of the icon to render, from the Bootstrap Icons list
        color: use this as Tabler color name to use as the foreground
            font color, leaving the background transparent.  If ``background``
            is also set, this is ignored.  Look at `Tabler: Colors
            <https://preview.tabler.io/docs/colors.html>`_
            for your choices; set this to the text after the ``bg-``
        background: use this as Tabler background/foreground color set for
            this icon.  : This overrides :py:attr:`color`. Look
            at `Tabler: Colors <https://preview.tabler.io/docs/colors.html>`_
            for your choices; set this to the text after the ``bg-``

    """

    tag: str = "i"
    block: str = "fonticon"

    #: The icon font family prefix.  One could override this to use FontAwesome icons,
    #: for instance, buy changing it to ``fa``
    prefix: str = "bi"

    #: Use this as the name for the icon to render
    icon: str
    #: If not ``None``, use this as Tabler color name to use as the foreground
    #: font color, leaving the background transparent.  If :py:attr:`background`
    #: is also set, this is ignored.  Look at `Tabler: Colors
    # <https://preview.tabler.io/docs/colors.html>`_  for your choices; set
    #: this to the text after the ``bg-``
    color: str | None = None
    #: If not ``None``, use this as Tabler background/foreground color set for
    #: this icon.  : This overrides :py:attr:`color`. Look
    #: at `Tabler: Colors <https://preview.tabler.io/docs/colors.html>`_
    #: for your choices; set this to the text after the ``bg-``
    background: str | None = None

    def __init__(
        self,
        icon: str | None = None,
        color: str | None = None,
        background: str | None = None,
        **kwargs: Any,
    ) -> None:
        self.icon = icon if icon else self.icon
        if not self.icon:
            # If icon is not set, we can't render this widget
            msg = "icon must be defined as a keyword argument or class attribute"
            raise ImproperlyConfigured(msg)
        if not isinstance(self.icon, str):
            # If icon is not a string, we can't render this widget
            msg = f"icon must be a string, not {type(self.icon).__name__}"
            raise ImproperlyConfigured(msg)
        super().__init__(**kwargs)
        self.color = color if color else self.color
        self.background = background if background else self.background
        self.icon = f"{self.prefix}-{icon}"
        self.add_class(self.icon)
        if self.color:
            self.add_class(f"text-{self.color} bg-transparent")
        elif self.background:
            self.add_class(f" bg-{self.background} text-{self.background}-fg")


class TablerFontIcon(FontIcon):
    """
    :py:class:`FontIcon` for Tabler Icons.

    You must include the Tabler Icons CSS in your HTML template:

    .. code-block:: html

        <link rel="stylesheet"
            href="https://cdn.jsdelivr.net/npm/@tabler/icons@latest/iconfont/tabler-icons.min.css">

    Example:
        .. code-block:: python

            from wildewidgets import TablerFontIcon

            icon = TablerFontIcon(icon="star")

    """

    prefix: str = "ti ti"


class TablerMenuIcon(FontIcon):
    """
    A Tabler menu specific icon.  This just adds some menu specific classes and
    uses a ``<span>`` instead of a ``<i>``.  It is used by
    :py:class:`wildewidgets.NavItem`, :py:class:`wildewidgets.NavDropdownItem`
    and :py:class:`wildewidgets.DropdownItem` objects.

    Typically, you won't use this directly, but instead it will be created for
    you from a :py:class:`wildewdigets.MenuItem` specification when
    :py:class:`wildewdigets.MenuItem.icon` is not ``None``.

    Example:
        .. code-block:: python

            from wildewidgets import NavItem, DropdownItem, NavDropdownItem
            from wildewidgets import TablerMenuIcon

            icon = TablerMenuIcon(icon='target')
            item = NavItem(text='Page', url='/page', icon=icon)
            item2 = DropdownItem(text='Page', url='/page', icon=icon)
            item3 = NavDropdownItem(text='Page', url='/page', icon=icon)

    """

    tag: str = "span"
    block: str = "nav-link-icon"
    css_class: str = "d-md-none d-lg-inline-block"
