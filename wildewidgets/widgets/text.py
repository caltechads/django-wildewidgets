#!/usr/bin/env python
# -*- coding: utf-8 -*-

import warnings
from typing import Optional

try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name
    from pygments.formatters import HtmlFormatter
except ModuleNotFoundError:
    # Only needed if using syntax highlighting
    pass

from .base import TemplateWidget, Block


class CodeWidget(Block):
    """
    A widget to display code with syntax highlighting if a language is supplied.

    Keyword Args:
        code: the code to be displayed
        language: the language of the code
        line_numbers: if ``True``, show line numbers
    """
    block: str = 'wildewidgets_highlight_container'

    #: The code to be displayed
    code: str = ""
    #: The programming language for the :py:attr:`code`
    language: Optional[str] = None
    #: If ``True``, show line numbers
    line_numbers: bool = False

    def __init__(
        self,
        code: str = None,
        language: str = None,
        line_numbers: bool = False,
        **kwargs
    ):
        self.code = code if code else self.code
        self.language = language if language else self.language
        if not self.language:
            raise ValueError(
                f'{self.__class__.__name__}: "language" must be defined either as a class attribute or a keyword arg'
            )
        self.line_numbers = line_numbers if line_numbers else self.line_numbers
        super().__init__(**kwargs)
        self.add_code(self.code, language=self.language, line_numbers=self.line_numbers)

    def add_code(self, code: str, language: str, line_numbers: bool = False) -> None:
        lexer = get_lexer_by_name(language)
        formatter = HtmlFormatter(linenos=line_numbers, cssclass="wildewidgets_highlight")
        self.add_block(highlight(code, lexer, formatter))


class MarkdownWidget(TemplateWidget):
    """
    A widget to display markdown as HTML.

    Args:
        text (str): the markdown to render as HTML.
        css_class (str, optional): any classes to add to the widget
    """
    template_name = 'wildewidgets/markdown_widget.html'
    text: str  = ""
    css_class: str = ""

    def __init__(self, *args, **kwargs):
        self.text = kwargs.pop("text", self.text)
        self.css_class = kwargs.pop("css_class", self.css_class)
        super().__init__(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        kwargs = super().get_context_data(*args, **kwargs)
        kwargs['text'] = self.text
        kwargs['css_class'] = self.css_class
        return kwargs


class HTMLWidget(TemplateWidget):
    """
    A widget to display raw HTML.

    Args:
        html (str): the HTML to render.
        css_class (str, optional): any classes to add to the widget
    """
    template_name = 'wildewidgets/html_widget.html'
    html = ""
    css_class = None

    def __init__(self, *args, **kwargs):
        self.html = kwargs.pop('html', self.html)
        self.css_class = kwargs.pop("css_class", self.css_class)
        super().__init__(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        kwargs = super().get_context_data(*args, **kwargs)
        kwargs['html'] = self.html
        kwargs['css_class'] = self.css_class
        return kwargs


class StringBlock(Block):
    """
    A basic widget that displays a string.

    .. deprecated:: 0.14.0

        Use :py:class:`wildewidgets.widgets.base.Block` directly instead.  It
        works exactly like :py:class:`StringBlock`

    Args:
        text: the text to display.
    """

    def __init__(self, text: str, **kwargs):
        warnings.warn(
            'Deprecated in 0.14.0; use Block directly instead.',
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*[text], **kwargs)


class TimeStamp(Block):
    """
    A basic widget that displays a timestamp.

    Args:
        text: the text to display.
    """
    tag = "small"
    css_class = "fw-light"


class TagBlock(Block):
    """
    A basic widget that displays a colored tag.

    Args:
        text: the text to display.
        color: the bootstrap color class.
    """
    block: str = 'badge'

    def __init__(self, text: str, color: str = "secondary", **kwargs):
        super().__init__(text, **kwargs)
        self.add_class(f'bg-{color}')
