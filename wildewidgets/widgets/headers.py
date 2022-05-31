#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .base import TemplateWidget
from .buttons import ModalButton, CollapseButton, LinkButton, FormButton

class BasicHeader(TemplateWidget):
    """Extends TemplateWidget.

    The base header class, which contains the bulk of the functionality.

    Args:
        header_level (str, optional): the header depth, as in h1, h2, h3...
        header_type (str, optional): the Boostrap 5 header class, either h-*, or display-*.
        header_text (str): the text of the header.
        css_class (str, optional): any css classes to apply to the header.
        css_id (str, optional): an ID to add to the header DIV.
        badge_text (str, optional): text to add in a badge to the right of the main header text.
        badge_class (str, optional): the css class to add to the badge. Default is 'warning'.
    """
    template_name = 'wildewidgets/header_with_controls.html'
    header_level = 1
    header_type = 'h'
    header_text = None
    css_class = "my-3"
    css_id = None
    badge_text = None
    badge_class = "warning"

    def __init__(self, **kwargs):
        self.header_level = kwargs.pop('header_level', self.header_level)
        self.header_type = kwargs.pop('header_type', self.header_type)
        self.header_text = kwargs.pop('header_text', self.header_text)
        self.css_class = kwargs.pop('css_class', self.css_class)
        self.css_id = kwargs.pop('css_id', self.css_id)
        self.badge_text = kwargs.pop('badge_text', self.badge_text)
        self.badge_class = kwargs.pop('badge_class', self.badge_class)
        super().__init__(title=self.header_text)

    def get_context_data(self, **kwargs):
        if self.header_type == 'h':
            kwargs['header_class'] = f"h{self.header_level}"
        elif self.header_type == 'display':
            kwargs['header_class'] = f"display-{self.header_level}"

        kwargs['header_level'] = self.header_level
        kwargs['header_text'] = self.header_text
        kwargs['header_type'] = self.header_type
        kwargs['css_class'] = self.css_class
        kwargs['css_id'] = self.css_id
        kwargs['badge_text'] = self.badge_text
        kwargs['badge_class'] = self.badge_class
        return kwargs


class HeaderWithLinkButton(BasicHeader):
    """Extends BasicHeader.

    This is deprecated. Use `HeaderWithWidget` instead.
    """
    template_name = 'wildewidgets/header_with_link_button.html'
    url = None
    link_text = None
    button_class = "primary"

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['url'] = self.url
        kwargs['link_text'] = self.link_text
        kwargs['button_class'] = self.button_class
        return kwargs


class HeaderWithFormButton(BasicHeader):
    """Extends BasicHeader.

    This is deprecated. Use `HeaderWithWidget` instead.
    """
    template_name = 'wildewidgets/header_with_form_button.html'
    url = None
    button_text = None

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['url'] = self.url
        kwargs['button_text'] = self.link_text
        return kwargs


class HeaderWithCollapseButton(BasicHeader):
    """Extends BasicHeader.

    This is deprecated. Use `HeaderWithWidget` instead.
    """
    template_name = 'wildewidgets/header_with_collapse_button.html'
    collapse_id = None
    button_text = None
    button_class = "primary"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.collapse_id = kwargs.get('collapse_id', self.collapse_id)
        self.button_text = kwargs.get('button_text', self.button_text)
        self.button_class = kwargs.get('button_class', self.button_class)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['collapse_id'] = self.collapse_id
        kwargs['button_text'] = self.button_text
        kwargs['button_class'] = self.button_class
        return kwargs


class HeaderWithModalButton(BasicHeader):
    """Extends BasicHeader.

    This is deprecated. Use `HeaderWithWidget` instead.
    """
    template_name = 'wildewidgets/header_with_modal_button.html'
    modal_id = None
    button_text = None
    button_class = "primary"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.modal_id = kwargs.get('modal_id', self.modal_id)
        self.button_text = kwargs.get('button_text', self.button_text)
        self.button_class = kwargs.get('button_class', self.button_class)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['modal_id'] = self.modal_id
        kwargs['button_text'] = self.button_text
        kwargs['button_class'] = self.button_class
        return kwargs


class HeaderWithWidget(BasicHeader):
    """Extends BasicHeader.

    The base class for more complex headers with buttons or other widgets attached. It can be 
    used stand-alone.

    Args:
        widget (obj): the widget to add to the header.
    """
    template_name = 'wildewidgets/header_with_widget.html'

    def __init__(self, widget=None, **kwargs):
        super().__init__(**kwargs)
        self.widget = widget

    def add_form_button(self, **kwargs):
        """
        Add a form button to the end of the headers. The arguments are those of the `FormButton`.
        """
        widget = FormButton(**kwargs)
        self.widget = widget

    def add_link_button(self, **kwargs):
        """
        Add a form button to the end of the headers. The arguments are those of the `LinkButton`.
        """
        widget = LinkButton(**kwargs)
        self.widget = widget

    def add_modal_button(self, **kwargs):
        """
        Add a form button to the end of the headers. The arguments are those of the `ModalButton`.
        """
        widget = ModalButton(**kwargs)
        self.widget = widget

    def add_collapse_button(self, **kwargs):
        """
        Add a form button to the end of the headers. The arguments are those of the `CollapseButton`.
        """
        widget = CollapseButton(**kwargs)
        self.widget = widget

    def set_widget(self, widget):
        """
        Add a widget to the header.
        """
        self.widget = widget

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['widget'] = self.widget
        return kwargs


class PageHeader(HeaderWithWidget):
    """Extends HeaderWithWidget.

    Provides a standard page header.
    """
    css_class = "my-4"


class CardHeader(HeaderWithWidget):
    """Extends HeaderWithWidget.

    Provides a standard card header.
    """
    css_class = "my-3"
    header_level = 2


class WidgetListLayoutHeader(HeaderWithWidget):
    """Extends HeaderWithWidget.

    Provides a standard WidgetListLayout header.
    """
    css_class = "mb-4"
    header_level = 2

