#!/usr/bin/env python
# -*- coding: utf-8 -*-
from copy import copy
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union

from .base import Widget, Block, WidgetStream
from .buttons import LinkButton, FormButton
from .headers import PageHeader, WidgetListLayoutHeader


@dataclass
class WidgetIndexItem:
    widget: Widget
    title: str
    icon: str = 'gear'


class WidgetIndex(Block):
    template_name: str = 'wildewidgets/widget_index.html'
    block: str = "widget-index"
    entries: List[WidgetIndexItem] = []

    def __init__(self, *args, **kwargs):
        entries = kwargs.pop('entries', copy(self.entries))
        super().__init__(*args, **kwargs)
        self._entries = entries

    @property
    def is_empty(self) -> bool:
        return len(self._entries) == 0

    def add_widget(self, widget, title=None, icon=None):
        """
        Add ``widget`` the index with title ``title`` and icon ``icon``.

        If ``title`` is ``None``, look for a title on ``widget.title``.  If that is also ``None``,
        default to the name of the widget class.

        If ``icon`` is ``None``, look for an icon on ``widget.icon``.  If that is also ``None``,
        default to the Bootstrap Icons "gear" icon.
        """
        if hasattr(widget, 'is_visible') and not widget.is_visible:
            return
        item = WidgetIndexItem(
            widget=widget,
            title=getattr(widget, 'title', widget.__class__.__name__),
            icon=getattr(widget, 'icon', 'gear')
        )
        if title is not None:
            item.title = title
        if icon is not None:
            item.icon = icon
        self._entries.append(item)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entries'] = self._entries
        return context


class WidgetListSidebarWidget(Block):
    template_name: str = 'wildewidgets/widget-list--sidebar.html'
    block: str = "widget-list__sidebar"
    css_class: Optional[str] = None
    actions: List[Widget] = []
    bare_widgets: List[Widget] = []

    class Widgets(WidgetStream):
        block: str = 'widget-list__sidebar__widgets'

    class Actions(WidgetStream):
        css_class: str = 'px-3 py-4 d-flex flex-column align-items-stretch border bg-white shadow-sm'

    def __init__(
        self,
        *args,
        title: str = None,
        width: int = 3,
        bare_widgets: List[Widget] = None,
        actions: List[Widget] = None,
        **kwargs
    ):
        if title is not None:
            self.title = title
        if self.css_class is None:
            self.css_class = ''
        self.css_class += f"col-{width}"
        super().__init__(*args, **kwargs)
        actions = actions if actions is not None else self.actions
        bare_widgets = bare_widgets if bare_widgets is not None else self.bare_widgets
        self.widget_index = WidgetIndex()
        self._widgets = WidgetListSidebarWidget.Widgets(widgets=bare_widgets)
        self._actions = WidgetListSidebarWidget.Actions(widgets=actions)
        self._actions.block = f"{self.block}__actions"

    def add_link_button(self, text: str, url: str, **kwargs):
        """
        Add :class:`wildewidgets.LinkButton` to the sidebar.

        :param text: use this as the button text
        :type text: str
        :param url: the URL for the link button
        :type url: str

        You may also use any of the keyword arguments for :class:`wildewidgets.LinkButton`.
        """
        kwargs['text'] = text
        kwargs['url'] = url
        if 'css_class' in kwargs:
            kwargs['css_class'] = f'{kwargs["css_class"]} w-100'
        else:
            kwargs['css_class'] = 'w-100'
        self.add_actions_widget(LinkButton(**kwargs))

    def add_form_button(self, text: str, action: str, **kwargs):
        """
        Add :class:`wildewidgets.FormButton` to the sidebar.

        :param text: use this as the button text
        :type text: str
        :param url: the URL for the link button
        :type url: str

        You may also use any of the keyword arguments for :class:`wildewidgets.FormButton`.
        """
        kwargs['text'] = text
        kwargs['action'] = action
        if 'css_class' in kwargs:
            kwargs['css_class'] = f'{kwargs["css_class"]} w-100'
        else:
            kwargs['css_class'] = 'w-100'
        if 'button_css_class' in kwargs:
            kwargs['button_css_class'] = f'{kwargs["button_css_class"]} w-100'
        else:
            kwargs['button_css_class'] = 'w-100'
        self.add_actions_widget(FormButton(**kwargs))

    def add_widget(self, widget: Widget):
        """
        Add a widget to the sidebar outside the Actions box.
        """
        self._widgets.add_widget(widget)

    def add_actions_widget(self, widget: Widget):
        """
        Add a widget to the sidebar inside the Actions box.
        """
        self._actions.add_widget(widget)

    def add_widget_to_index(self, widget: Widget, title: Optional[str] = None, icon: Optional[str] = None):
        """
        Add ``widget`` the index with title ``title`` and icon ``icon``.

        If ``title`` is ``None``, look for a title on ``widget.title``.  If that is also ``None``,
        default to the name of the widget class.

        If ``icon`` is ``None``, look for an icon on ``widget.icon``.  If that is also ``None``,
        default to the Bootstrap Icons "gear" icon.
        """
        self.widget_index.add_widget(widget, title=title, icon=icon)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        if not self._widgets.is_empty:
            context['widgets'] = self._widgets
            self.widget_index._css_class = 'mt-5'
        if not self._actions.is_empty:
            context['actions'] = self._actions
            self.widget_index._css_class = 'mt-5'
        if not self.widget_index.is_empty:
            context['widget_index'] = self.widget_index
        return context


class WidgetListMainWidget(Block):
    template_name: str = 'wildewidgets/widget-list--main.html'
    block: str = "widget-list__main"
    css_class: Optional[str] = 'col'
    entry_css_class: Optional[str] = 'shadow bg-white'
    entry_title_css_class: Optional[str] = 'font-weight-bold'
    entries: List[WidgetIndexItem] = []

    def __init__(self, *args, **kwargs):
        entries = kwargs.pop('entries', copy(self.entries))
        self._entry_css_class = kwargs.pop('entry_css_class', self.entry_css_class)
        self._entry_title_css_class = kwargs.pop('entry_title_css_class', self.entry_title_css_class)
        super().__init__(*args, **kwargs)
        self._entries: List[WidgetIndexItem] = entries

    def add_widget(self, widget: Widget, title: Optional[Union[str, Widget]] = None):
        if title is not None:
            widget.title = title
        widget_title = widget.get_title()
        if not isinstance(widget_title, Widget):
            header = WidgetListLayoutHeader(header_text=widget.title)
            widget.title = header
        self._entries.append(widget)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['entries'] = self._entries
        context['entry_title_css_class'] = self._entry_title_css_class
        context['entry_css_class'] = self._entry_css_class
        return context


class WidgetListLayout(Block):
    """
    Extend `Block`. This class provides a two column layout. The first column
    is the sidebar containing links to the various widgets in the right column,
    and the second column is the main content, consisting of the contained
    widgets vertically stacked.

    Example 1:

        layout = WidgetListLayout('My Page')
        layout.add_sidebar_form_button('Update', reverse('core:thing--update'))
        layout.add_widget(Widget1(), title='another title')
        layout.add_widget(Widget2(), title='the title', icon='stuff')
        layout.add_widget(Widget3())

    """
    template_name: str = 'wildewidgets/widget-list.html'
    sidebar_title: str = 'Actions'
    # Number of columns
    sidebar_width: int = 3

    def __init__(self, title: str, sidebar_title: str = None, sidebar_width: int = None, **kwargs) -> None:
        """
        Extend `Block.__init__()`.

        Parameters
        ----------
        title : str
            The title of the widget.
        sidebar_title: str
            Use this for the title of the sidebar column, otherwise use cls.sidebar_title
        sidebar_width: int
            Use this for the width in columns of the sidebar column, otherwise use cls.sidebar_width
        """
        super().__init__(**kwargs)
        self.title = title
        self.header: Widget = PageHeader(header_text=title)
        self.sidebar: Widget = WidgetListSidebarWidget(
            title=sidebar_title if sidebar_title is not None else self.sidebar_title,
            width=sidebar_width if sidebar_width is not None else self.sidebar_width
        )
        self.main = WidgetListMainWidget()
        self.modals: List[Widget] = []

    def add_widget(self, widget: Widget, title: Optional[str] = None, icon: Optional[str] = None) -> None:
        self.sidebar.add_widget_to_index(widget, title=title, icon=icon)
        self.main.add_widget(widget, title=title)

    def add_modal(self, modal: Widget) -> None:
        self.modals.append(modal)

    def add_sidebar_link_button(self, text: str, url: str, **kwargs) -> None:
        self.sidebar.add_link_button(text, url, **kwargs)

    def add_sidebar_form_button(self, text: str, action: str, **kwargs) -> None:
        self.sidebar.add_form_button(text, action, **kwargs)

    def add_sidebar_widget(self, widget: Widget) -> None:
        self.sidebar.add_actions_widget(widget)

    def add_sidebar_bare_widget(self, widget: Widget) -> None:
        self.sidebar.add_widget(widget)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['sidebar'] = self.sidebar
        context['sidebar_width'] = self.sidebar_width
        context['main'] = self.main
        context['modals'] = self.modals
        context['header'] = self.header
        return context
