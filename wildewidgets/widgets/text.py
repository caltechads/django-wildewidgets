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
    """Extends TemplateWidget.

    A widget to display code with context-sensitive if a language is supplied.

    Args:
        code (str): the code to be displayed
        language (str): the language of the code
    """
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
    """
    Extends :py:class:`wildewidgets.widgets.base.TemplateWidget`.

    A widget to display markdown as HTML.

    Args:
        text (str): the markdown to render as HTML.
        css_class (str, optional): any classes to add to the widget
    """
    template_name = 'wildewidgets/markdown_widget.html'
    text = ""
    css_class = ""

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.text = kwargs.get("text", self.text)
        self.css_class = kwargs.get("css_class", self.css_class)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['text'] = self.text
        kwargs['css_class'] = self.css_class
        return kwargs


class HTMLWidget(TemplateWidget):
    """
    Extends :py:class:`wildewidgets.widgets.base.TemplateWidget`.

    A widget to display raw HTML.

    Args:
        html (str): the HTML to render.
        css_class (str, optional): any classes to add to the widget
    """
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
    """
    Extends :py:class:`wildewidgets.widgets.base.Block`.

    A basic widget that displays a string.

    .. deprecated::

        Use :py:class:`wildewidgets.widgets.base.Block` directly instead.  It
        works exactly like :py:class:`StringBlock`

    Args:
        text: the text to display.
    """

    def __init__(self, text: str, **kwargs):
        warnings.warn(
            'Deprecated in 0.16.0; use Block directly instead.',
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*[text], **kwargs)


class TimeStamp(Block):
    """
    Extends :py:class:`wildewidgets.widgets.base.Block`.

    A basic widget that displays a timestamp.

    Args:
        text: the text to display.
    """
    tag = "small"
    css_class = "fw-light"


class LabelBlock(Block):
    """
    Extends :py:class:`wildewidgets.widgets.base.Block`.

    A ``<label>``.

    Args:
        text: the text to display.
    """
    tag: str = "label"

    def __init__(self, text: str, color: str = "secondary", **kwargs):
        # FIXME: color is a kwarg, but it is not used
        super().__init__(text, **kwargs)
        self.add_class('fw-bold')


class TagBlock(Block):
    """
    Extends :py:class:`wildewidgets.widgets.base.Block`.

    A basic widget that displays a colored tag.

    Args:
        text: the text to display.
        color: the bootstrap color class.
    """
    block: str = 'badge'

    def __init__(self, text: str, color: str = "secondary", **kwargs):
        super().__init__(text, **kwargs)
        self.add_class(f'bg-{color}')
