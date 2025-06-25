from __future__ import annotations

from copy import copy
from dataclasses import dataclass
from typing import Any

from .base import Block, Widget, WidgetStream
from .buttons import FormButton, LinkButton
from .headers import PageHeader, WidgetListLayoutHeader


@dataclass
class WidgetIndexItem:
    """
    Data container for items in a widget index.

    This dataclass represents a single entry in a widget index, combining
    a widget instance with its display title and icon.

    Attributes:
        widget: The widget instance to be displayed in the index
        title: Display title for the widget in the index
        icon: Icon identifier to display next to the widget title, defaults to "gear"

    """

    widget: Widget
    title: str
    icon: str = "gear"


class WidgetIndex(Block):
    """
    A navigational index of widgets.

    This widget creates a visual index or table of contents for a collection
    of widgets. Each entry in the index consists of a widget with an associated
    title and icon.

    Note:
        This is not something that you would use directly.
        :py:class:`WidgetListLayout` uses this internally when you add widgets
        to the main content area.

    Attributes:
        template_name: Path to the template used to render the widget index
        block: CSS block name for styling
        entries: Default list of widget index items

    Args:
        *args: Positional arguments passed to parent

    Keyword Args:
        **kwargs: Keyword arguments which may include 'entries' to
            initialize the index with a list of :py:class:`WidgetIndexItem` objects


    """

    template_name: str = "wildewidgets/widget_index.html"
    block: str = "widget-index"
    entries: list[WidgetIndexItem] = []  # noqa: RUF012

    def __init__(self, *args, **kwargs):
        """
        Initialize a widget index.

        """
        entries = kwargs.pop("entries", copy(self.entries))
        super().__init__(*args, **kwargs)
        self._entries = entries

    @property
    def is_empty(self) -> bool:
        """
        Check if the widget index is empty.

        Returns:
            bool: True if the index contains no entries, False otherwise

        """
        return len(self._entries) == 0

    def add_widget(
        self, widget: Widget, title: str | None = None, icon: str | None = None
    ) -> None:
        """
        Add a widget to the index.

        Adds the given widget to the index with an associated title and icon.
        If title or icon are not provided, they will be determined from the
        widget attributes or defaults.

        Note:
            If the widget has an is_visible function that evaluates to False,
            the widget will not be added to the index.

        Args:
            widget: The widget to add to the index
            title: Optional display title for the widget. If None, uses `widget.title1`
                  or the widget class name
            icon: Optional icon identifier. If None, uses widget.icon or "gear"

        """
        if hasattr(widget, "is_visible") and not widget.is_visible():
            return
        item = WidgetIndexItem(
            widget=widget,
            title=getattr(widget, "title", widget.__class__.__name__),
            icon=getattr(widget, "icon", "gear"),
        )
        if title is not None:
            item.title = title
        if icon is not None:
            item.icon = icon
        self._entries.append(item)

    def get_context_data(self, *args, **kwargs) -> dict[str, Any]:
        """
        Get context data for template rendering.

        Adds the widget index entries to the template context.

        Args:
            *args: Positional arguments passed to parent
            **kwargs: Additional context variables

        Returns:
            dict: Updated context dictionary with entries

        """
        context = super().get_context_data(*args, **kwargs)
        context["entries"] = self._entries
        return context


class WidgetListSidebarWidget(Block):
    """
    A sidebar component for widget list layouts.

    This widget creates a sidebar that can contain actions (typically buttons)
    and other widgets. It's commonly used as part of a WidgetListLayout to
    provide navigation and action controls.

    Note:
        This is not something that you would use directly.
        :py:class:`WidgetListLayout` uses this internally when you add widgets
        to the sidebar area.

    Attributes:
        template_name: Path to the template used to render the sidebar
        block: CSS block name for styling
        css_class: CSS classes to apply to the sidebar
        actions: Default list of action widgets to display
        bare_widgets: Default list of widgets to display without special styling

    Args:
        *args: Positional arguments passed to parent

    Keyword Args:
        title: Optional title for the sidebar
        width: Column width for the sidebar, defaults to 3
        breakpoint: Bootstrap breakpoint for responsive design
        bare_widgets: Optional list of widgets to display without special styling
        actions: Optional list of action widgets to display
        **kwargs: Additional keyword arguments passed to parent

    """

    template_name: str = "wildewidgets/widget-list--sidebar.html"

    block: str = "widget-list__sidebar"
    css_class: str = ""
    actions: list[Widget] = []  # noqa: RUF012
    bare_widgets: list[Widget] = []  # noqa: RUF012

    class Widgets(WidgetStream):
        block: str = "widget-list__sidebar__widgets"

    class Actions(WidgetStream):
        css_class: str = (
            "px-3 py-4 d-flex flex-column align-items-stretch border bg-white shadow-sm"
        )

    def __init__(
        self,
        *args,
        title: str | None = None,
        width: int = 3,
        breakpoint: str = "xl",  # noqa: A002
        bare_widgets: list[Widget] | None = None,
        actions: list[Widget] | None = None,
        **kwargs,
    ):
        if title is not None:
            self.title = title
        if self.css_class is None:
            self.css_class = ""
        if breakpoint:
            self.css_class += f"col-{breakpoint}-{width}"
        else:
            self.css_class += f"col-{width}"
        super().__init__(*args, **kwargs)
        actions = actions if actions is not None else self.actions
        bare_widgets = bare_widgets if bare_widgets is not None else self.bare_widgets
        self.widget_index = WidgetIndex()
        self._widgets = WidgetListSidebarWidget.Widgets(widgets=bare_widgets)
        self._actions = WidgetListSidebarWidget.Actions(widgets=actions)
        self._actions.block = f"{self.block}__actions"

    def add_link_button(self, text: str, url: str, **kwargs) -> None:
        """
        Add :class:`wildewidgets.LinkButton` to the sidebar.

        Args:
            text: The text to display on the button.
            url: The URL to link to.

        Keyword Args:
            **kwargs: any additional keyword arguments appropriate for
                      :class:`wildewidgets.FormButton`

        """
        kwargs["text"] = text
        kwargs["url"] = url
        if "css_class" in kwargs:
            kwargs["css_class"] = f"{kwargs['css_class']} w-100"
        else:
            kwargs["css_class"] = "w-100"
        self.add_actions_widget(LinkButton(**kwargs))

    def add_form_button(self, text: str, action: str, **kwargs) -> None:
        """
        Add :class:`wildewidgets.FormButton` to the sidebar.

        Args:
            text: The text to display on the button.
            action: The action to perform when the button is clicked.

        Keyword Args:
            **kwargs: any additional keyword arguments appropriate for
                      :class:`wildewidgets.FormButton`

        """
        kwargs["text"] = text
        kwargs["action"] = action
        if "css_class" in kwargs:
            kwargs["css_class"] = f"{kwargs['css_class']} w-100"
        else:
            kwargs["css_class"] = "w-100"
        if "button_css_class" in kwargs:
            kwargs["button_css_class"] = f"{kwargs['button_css_class']} w-100"
        else:
            kwargs["button_css_class"] = "w-100"
        self.add_actions_widget(FormButton(**kwargs))

    def add_widget(self, widget: Widget) -> None:
        """
        Add a widget to the sidebar outside the Actions box.
        """
        self._widgets.add_widget(widget)

    def add_actions_widget(self, widget: Widget) -> None:
        """
        Add a widget to the sidebar inside the Actions box.
        """
        self._actions.add_widget(widget)

    def add_widget_to_index(
        self, widget: Widget, title: str | None = None, icon: str | None = None
    ) -> None:
        """
        Add ``widget`` the index with title ``title`` and icon ``icon``.

        If ``title`` is ``None``, look for a title on ``widget.title``.  If that
        is also ``None``, default to the name of the widget class.

        If ``icon`` is ``None``, look for an icon on ``widget.icon``.  If that
        is also ``None``, default to the Bootstrap Icons "gear" icon.
        """
        self.widget_index.add_widget(widget, title=title, icon=icon)

    def get_context_data(self, *args, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(*args, **kwargs)
        context["title"] = self.title
        if not self._widgets.is_empty:
            context["widgets"] = self._widgets
            self.widget_index._css_class = "mt-5"
        if not self._actions.is_empty:
            context["actions"] = self._actions
            self.widget_index._css_class = "mt-5"
        if not self.widget_index.is_empty:
            context["widget_index"] = self.widget_index
        return context


class WidgetListMainWidget(Block):
    """
    The main content area in a widget list layout.

    This widget represents the primary content area where widgets are displayed
    in a vertical stack. It's typically used in conjunction with a sidebar
    widget to create a comprehensive layout.

    Note:
        This is not something that you would use directly.
        :py:class:`WidgetListLayout` uses this internally when you add widgets
        to the main area.

    Attributes:
        template_name: Path to the template used to render the main widget list
        block: CSS block name for styling
        css_class: CSS class for the main content area
        entry_css_class: CSS class for individual widget entries
        entry_title_css_class: CSS class for widget entry titles
        entries: Default list of widget index items for the main content

    Args:
        *args: Positional arguments passed to parent

    Keyword Args:
        **kwargs: Keyword arguments which may include 'entries' to
            initialize the list with a list of WidgetIndexItem objects


    """

    template_name: str = "wildewidgets/widget-list--main.html"
    block: str = "widget-list__main"

    css_class: str = "col"
    entry_css_class: str | None = "shadow bg-white"
    entry_title_css_class: str | None = "font-weight-bold"
    entries: list[Widget] = []  # noqa: RUF012

    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize the main widget list.

        """
        entries = kwargs.pop("entries", copy(self.entries))
        self._entry_css_class = kwargs.pop("entry_css_class", self.entry_css_class)
        self._entry_title_css_class = kwargs.pop(
            "entry_title_css_class", self.entry_title_css_class
        )
        super().__init__(*args, **kwargs)
        self._entries: list[Widget] = entries

    def add_widget(self, widget: Widget, title: str | Widget | None = None) -> None:
        """
        Add a widget to the main content area.

        This method also ensures that the widget has an associated title,
        either from the widget itself or as a provided argument.

        Args:
            widget: The widget to add to the main content area
            title: Optional title for the widget. If provided, it will be
                   set as the widget's title attribute

        """
        if hasattr(widget, "is_visible") and not widget.is_visible():
            return
        if title is not None:
            widget.title = title
        widget_title = widget.get_title()
        if not isinstance(widget_title, Widget):
            header = WidgetListLayoutHeader(header_text=widget.title)
            widget.title = header
        self._entries.append(widget)

    def get_context_data(self, *args, **kwargs) -> dict[str, Any]:
        """
        Get context data for template rendering.

        Provides the list of entries to be rendered in the main widget area.

        Args:
            *args: Positional arguments passed to parent
            **kwargs: Additional context variables

        Returns:
            dict: Updated context dictionary with entries and CSS classes

        """
        context = super().get_context_data(*args, **kwargs)
        context["entries"] = self._entries
        context["entry_title_css_class"] = self._entry_title_css_class
        context["entry_css_class"] = self._entry_css_class
        return context


class WidgetListLayout(Block):
    """
    Provides a two column layout. The first column is the sidebar containing
    links to the various widgets in the right column, and the second column is
    the main content, consisting of the contained widgets vertically stacked.

    This is really the only class you need to use to create a page with a
    sidebar and a main content area.  You can add widgets to the sidebar and
    the main content area, and they will be displayed in the appropriate places.

    Example:
        .. code-block:: python

            from wildewidgets import WidgetListLayout
            from django.urls import reverse
            from core.widgets import Widget1, Widget2, Widget3

            layout = WidgetListLayout('My Page')
            layout.add_sidebar_form_button('Update', reverse('core:thing--update'))
            layout.add_widget(Widget1(), title='another title')
            layout.add_widget(Widget2(), title='the title', icon='stuff')
            layout.add_widget(Widget3())

    Keyword Args:
        title: The title of the widget.
        sidebar_title: the title of the sidebar column
        sidebar_width: the width in columns of the sidebar column
        sidebar_breakpoint: the breakpoint at which the sidebar will collapse
            to a hamburger menu.  Defaults to "xl" (extra large).
        **kwargs: Additional keyword arguments passed to the parent
            *:py:class:`wildewidgets.Block` class

    """

    #: The Django template to render this layout.
    template_name: str = "wildewidgets/widget-list.html"
    #: The title of the sidebar column.
    sidebar_title: str = "Actions"
    #: The width of the sidebar column in Bootstrap grid columns.
    sidebar_width: int = 3
    #: The breakpoint at which the sidebar will collapse to a hamburger menu.
    sidebar_breakpoint: str = "xl"

    def __init__(
        self,
        title: str,
        sidebar_title: str | None = None,
        sidebar_width: int | None = None,
        sidebar_breakpoint: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.title = title
        self.header: Widget = PageHeader(header_text=title)
        self.sidebar: Widget = WidgetListSidebarWidget(
            title=sidebar_title if sidebar_title is not None else self.sidebar_title,
            width=sidebar_width if sidebar_width is not None else self.sidebar_width,
            breakpoint=sidebar_breakpoint
            if sidebar_breakpoint is not None
            else self.sidebar_breakpoint,
        )
        self.main = WidgetListMainWidget()
        self.modals: list[Widget] = []

    def add_widget(
        self, widget: Widget, title: str | None = None, icon: str | None = None
    ) -> None:
        """
        Add a widget to the layout.

        This method adds the widget to both the sidebar index and the main
        content area.

        Args:
            widget: The widget to add
            title: Optional title for the widget
            icon: Optional icon for the widget

        """
        self.sidebar.add_widget_to_index(widget, title=title, icon=icon)
        self.main.add_widget(widget, title=title)

    def add_modal(self, modal: Widget) -> None:
        """
        Add a modal widget to the layout.

        Modals are typically used for dialogs or secondary content that
        overlays the main content.

        Args:
            modal: The modal widget to add

        Returns:
            None

        """
        self.modals.append(modal)

    def add_sidebar_link_button(self, text: str, url: str, **kwargs) -> None:
        """
        Add a link button to the sidebar.

        This method simplifies the addition of link buttons to the sidebar
        with appropriate styling and behavior.

        Args:
            text: The text to display on the button
            url: The URL that the button should link to
            **kwargs: Additional keyword arguments for customization

        """
        self.sidebar.add_link_button(text, url, **kwargs)

    def add_sidebar_form_button(self, text: str, action: str, **kwargs) -> None:
        """
        Add a form button to the sidebar.

        This method simplifies the addition of form buttons to the sidebar
        with appropriate styling and behavior.

        Args:
            text: The text to display on the button
            action: The form action URL that the button should submit to
            **kwargs: Additional keyword arguments for customization

        """
        self.sidebar.add_form_button(text, action, **kwargs)

    def add_sidebar_widget(self, widget: Widget) -> None:
        """
        Add a widget to the sidebar.

        This method adds the widget to the Actions area of the sidebar,
        typically used for secondary actions or information.

        Args:
            widget: The widget to add to the sidebar

        """
        self.sidebar.add_actions_widget(widget)

    def add_sidebar_bare_widget(self, widget: Widget) -> None:
        """
        Add a bare widget to the sidebar.

        Bare widgets are added outside the Actions area and are not
        subject to special styling.

        Args:
            widget: The widget to add to the sidebar

        """
        self.sidebar.add_widget(widget)

    def get_context_data(self, *args, **kwargs) -> dict[str, Any]:
        """
        Get context data for template rendering.

        Provides the layout with the necessary context variables for
        rendering the title, sidebar, main content, and any modals.

        Args:
            *args: Positional arguments passed to parent
            **kwargs: Additional context variables

        Returns:
            dict: Updated context dictionary with layout components

        """
        context = super().get_context_data(*args, **kwargs)
        context["title"] = self.title
        context["sidebar"] = self.sidebar
        context["sidebar_width"] = self.sidebar_width
        context["main"] = self.main
        context["modals"] = self.modals
        context["header"] = self.header
        return context
