#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random

from .base import TemplateWidget

from django.core.exceptions import ImproperlyConfigured


class TabbedWidget(TemplateWidget):
    template_name = 'wildewidgets/tabbed_widget.html'
    slug_suffix = None

    def __init__(self, *args, **kwargs):
        self.tabs = []

    def add_tab(self, name, widget):
        self.tabs.append((name, widget))

    def get_context_data(self, **kwargs):
        kwargs['tabs'] = self.tabs
        if not self.slug_suffix:
            self.slug_suffix = random.randrange(0, 10000)
        kwargs['identifier'] = self.slug_suffix
        return kwargs


class CardWidget(TemplateWidget):
    template_name = 'wildewidgets/card.html'
    header = None
    header_text = None
    title = None
    subtitle = None
    widget = None
    widget_css = None
    css_class = None

    def __init__(self, **kwargs):
        self.header = kwargs.get('header', self.header)
        self.header_text = kwargs.get('header_text', self.header_text)
        self.title = kwargs.get('title', self.title)
        self.subtitle = kwargs.get('subtitle', self.subtitle)
        self.widget = kwargs.get('widget', self.widget)
        self.widget_css = kwargs.get('widget_css', self.widget_css)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['header'] = self.header
        kwargs['header_text'] = self.header_text
        kwargs['title'] = self.title
        kwargs['subtitle'] = self.subtitle
        kwargs['widget'] = self.widget
        kwargs['widget_css'] = self.widget_css
        kwargs['css_class'] = self.css_class

        if not self.widget:
            raise ImproperlyConfigured("You must define a widget.")
        return kwargs

    def set_widget(self, widget, css_class=None):
        self.widget = widget
        self.widget_css = css_class

    def set_header(self, header):
        self.header = header
