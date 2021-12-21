#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name
    from pygments.formatters import HtmlFormatter
except ModuleNotFoundError:
    # Only needed if using syntax highlighting
    pass

from django.core.exceptions import ImproperlyConfigured

from .base import TemplateWidget


class CodeWidget(TemplateWidget):
    template_name = 'wildewidgets/code_widget.html'
    language = None
    code = ""
    Line_numbers = False
    css_class = None

    def __init__(self, *args, **kwargs):
        if 'code' in kwargs:
            self.code = kwargs['code']
        if 'language' in kwargs:
            self.language = kwargs['language']

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        if not self.language:
            raise ImproperlyConfigured("You must define a language.")
        lexer = get_lexer_by_name(self.language)
        formatter = HtmlFormatter(linenos=self.Line_numbers, cssclass="wildewidgets_highlight")
        kwargs['code'] = highlight(self.code, lexer, formatter)
        kwargs['css_class'] = self.css_class
        return kwargs


class MarkdownWidget(TemplateWidget):
    template_name = 'wildewidgets/markdown_widget.html'
    text = ""
    css_class = None

    def __init__(self, *args, **kwargs):
        if 'text' in kwargs:
            self.text = kwargs['text']

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['text'] = self.text
        kwargs['css_class'] = self.css_class
        return kwargs


class HTMLWidget(TemplateWidget):
    template_name = 'wildewidgets/html_widget.html'
    html = ""
    css_class = None

    def __init__(self, *args, **kwargs):
        self.html = kwargs.get('html', self.html)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['html'] = self.html
        kwargs['css_class'] = self.css_class
        return kwargs
