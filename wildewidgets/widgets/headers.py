#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Optional
import warnings

from .base import TemplateWidget, Block
from .buttons import ModalButton, CollapseButton, LinkButton, FormButton


class BasicHeader(TemplateWidget):
    """
    The base header class, which contains the bulk of the functionality.

    Keyword Args:
        header_level: the header depth, as in h1, h2, h3...
        header_type: the Boostrap 5 header class, either h-*, or display-*.
        header_text: the text of the header.
        css_class: any css classes to apply to the header.
        css_id: an ID to add to the header div.
        badge_text: text to add in a badge to the right of the main header text.
        badge_class: the css class to add to the badge.
    """
    template_name: str = 'wildewidgets/header_with_controls.html'

    header_level: int = 1
    header_type: str = 'h'
    header_text: Optional[str] = None
    css_class: str = "my-3"
    css_id: Optional[str] = None
    badge_text: Optional[str] = None
    badge_class: str = "warning"
    badge_rounded_pill: bool = True

    def __init__(
        self,
        header_level: int = None,
        header_type: str = None,
        header_text: str = None,
        css_class: str = None,
        css_id: str = None,
        badge_text: str = None,
        badge_class: str = None,
        badge_rounded_pill: bool = None,
        **kwargs
    ):
        self.header_level = header_level if header_level else self.header_level
        self.header_type = header_type if header_type else self.header_type
        self.header_text = header_text if header_text else self.header_text
        self.css_class = css_class if css_class else self.css_class
        self.css_id = css_id if css_id else self.css_id
        self.badge_text = badge_text if badge_text else self.badge_text
        self.badge_class = badge_class if badge_class else self.badge_class
        self.badge_rounded_pill = badge_rounded_pill if badge_rounded_pill else self.badge_rounded_pill
        kwargs['title'] = self.header_text
        super().__init__(**kwargs)

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
        kwargs['badge_rounded_pill'] = self.badge_rounded_pill
        return kwargs


class HeaderWithLinkButton(BasicHeader):
    """
    Header with button that links to something.

    .. deprecated:: 0.13.45
        Use :py:class:`HeaderWithWidget` instead.
    """
    template_name = 'wildewidgets/header_with_link_button.html'

    url: Optional[str] = None
    link_text: Optional[str] = None
    button_class: str = "primary"

    def __init__(
        self,
        url: str = None,
        link_text: str = None,
        button_class: str = None,
        **kwargs
    ):
        warnings.warn('Use wildewidgets.HeaderWithWidget instead', DeprecationWarning, stacklevel=2)
        self.url = url if url else self.url
        self.link_text = link_text if link_text else self.link_text
        self.button_class = button_class if button_class else self.button_class
        super().__init__(**kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['url'] = self.url
        kwargs['link_text'] = self.link_text
        kwargs['button_class'] = self.button_class
        return kwargs


class HeaderWithFormButton(BasicHeader):
    """
    Header with a button that submits a form.

    .. deprecated:: 0.13.45
        Use :py:class:`HeaderWithWidget` instead.
    """
    template_name = 'wildewidgets/header_with_form_button.html'

    url: Optional[str] = None
    button_text: Optional[str] = None

    def __init__(
        self,
        url: str = None,
        button_text: str = None,
        **kwargs
    ):
        warnings.warn('Use wildewidgets.HeaderWithWidget instead', DeprecationWarning, stacklevel=2)
        self.url = url if url else self.url
        self.button_text = button_text if button_text else self.button_text
        super().__init__(**kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['url'] = self.url
        kwargs['button_text'] = self.button_text
        return kwargs


class HeaderWithCollapseButton(BasicHeader):
    """
    .. deprecated:: 0.13.45
        Use :py:class:`HeaderWithWidget` instead.
    """
    template_name: str = 'wildewidgets/header_with_collapse_button.html'

    collapse_id: Optional[str] = None
    button_text: Optional[str] = None
    button_class: Optional[str] = "primary"

    def __init__(
        self,
        collapse_id: str = None,
        button_text: str = None,
        button_class: str = None,
        **kwargs
    ):
        warnings.warn('Use wildewidgets.HeaderWithWidget instead', DeprecationWarning, stacklevel=2)
        self.collapse_id = collapse_id if collapse_id else self.collapse_id
        self.button_text = button_text if button_text else self.button_text
        self.button_class = button_class if button_class else self.button_class
        super().__init__(**kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['collapse_id'] = self.collapse_id
        kwargs['button_text'] = self.button_text
        kwargs['button_class'] = self.button_class
        return kwargs


class HeaderWithModalButton(BasicHeader):
    """
    .. deprecated:: 0.13.45
        Use :py:class:`HeaderWithWidget` instead.
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
    """
    The base class for more complex headers with buttons or other widgets
    attached. It can be used stand-alone.

    Keyword Args:
        widget: the widget to add to the header.
    """
    template_name = 'wildewidgets/header_with_widget.html'

    def __init__(self, widget: Block = None, **kwargs):
        super().__init__(**kwargs)
        self.widget = widget

    def add_form_button(self, **kwargs):
        """
        Add a form button to the end of the headers. The arguments are those of the :py:class:`wildewidgets.FormButton`.
        """
        self.widget = FormButton(**kwargs)

    def add_link_button(self, **kwargs):
        """
        Add a form button to the end of the headers. The arguments are those of the :py:class:`wildewidgets.LinkButton`.
        """
        self.widget = LinkButton(**kwargs)

    def add_modal_button(self, **kwargs):
        """
        Add a modal button to the end of the headers. The arguments are those of
        the :py:class:`wildewidgets.ModalButton`.
        """
        self.widget = ModalButton(**kwargs)

    def add_collapse_button(self, **kwargs):
        """
        Add a form button to the end of the headers. The arguments are those of
        the :py:class:`wildewidgets.CollapseButton`.
        """
        self.widget = CollapseButton(**kwargs)

    def set_widget(self, widget: Block):
        """
        Add a widget to the header.
        """
        self.widget = widget

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['widget'] = self.widget
        return kwargs


class PageHeader(HeaderWithWidget):
    """
    Provides a standard page header.
    """
    css_class: str = "my-4"


class CardHeader(HeaderWithWidget):
    """
    Provides a standard card header.
    """
    css_class: str = "my-3"
    header_level: int = 2


class WidgetListLayoutHeader(HeaderWithWidget):
    """
    Provides a standard :py:class:`wildewidgets.WidgetListLayout` header.
    """
    css_class: str = "mb-4"
    header_level: int = 2
