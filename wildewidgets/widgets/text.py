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

from .base import TemplateWidget, Block


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
        self.css_class = kwargs.get("css_class", self.css_class)

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
    css_class = ""

    def __init__(self, *args, **kwargs):
        self.text = kwargs.get("text", self.text)
        self.css_class = kwargs.get("css_class", self.css_class)

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
        self.css_class = kwargs.get("css_class", self.css_class)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['html'] = self.html
        kwargs['css_class'] = self.css_class
        return kwargs


class StringBlock(Block):

    def __init__(self, text: str, **kwargs):
        super().__init__(*[text], **kwargs)


class TimeStamp(StringBlock):
    tag="small"
    css_class="fw-light"


class LabelBlock(StringBlock):

    def __init__(self, text: str, color: str = "secondary", **kwargs):
        css_class = kwargs.get("css_class", "")
        css_class += f" fw-bold"
        kwargs["css_class"] = css_class.strip()
        super().__init__(text, **kwargs)


class TagBlock(StringBlock):

    def __init__(self, text: str, color: str = "secondary", **kwargs):
        css_class = kwargs.get("css_class", "")
        css_class += f" badge bg-{color}"
        kwargs["css_class"] = css_class.strip()
        super().__init__(text, **kwargs)

