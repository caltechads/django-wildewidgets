#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .base import TemplateWidget


class BasicHeader(TemplateWidget):
    template_name = 'wildewidgets/header_with_controls.html'
    header_level = 1
    header_type = 'h'
    header_text = None
    css_class = "my-3"
    css_id = None
    badge_text = None
    badge_class = "warning"

    def __init__(self, **kwargs):
        self.header_level = kwargs.get('header_level', self.header_level)
        self.header_type = kwargs.get('header_type', self.header_type)
        self.header_text = kwargs.get('header_text', self.header_text)
        self.css_class = kwargs.get('css_class', self.css_class)
        self.css_id = kwargs.get('css_id', self.css_id)
        self.badge_text = kwargs.get('badge_text', self.badge_text)
        self.badge_class = kwargs.get('badge_class', self.badge_class)

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
    template_name = 'wildewidgets/header_with_form_button.html'
    url = None
    button_text = None

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['url'] = self.url
        kwargs['button_text'] = self.link_text
        return kwargs


class HeaderWithCollapseButton(BasicHeader):
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
    template_name = 'wildewidgets/header_with_widget.html'

    def __init__(self, **kwargs):
        super().__init__()
        self.widget = kwargs.get('widget', None)

    def set_widget(self, widget):
        self.widget = widget

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['widget'] = self.widget
        return kwargs
