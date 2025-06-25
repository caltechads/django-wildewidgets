from __future__ import annotations

import warnings
from typing import Any

try:
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import get_lexer_by_name
except ModuleNotFoundError:
    # Only needed if using syntax highlighting
    pass

from .base import Block, TemplateWidget


class CodeWidget(Block):
    """
    A widget that displays code with syntax highlighting.

    This widget uses Pygments to apply syntax highlighting to code snippets.
    The programming language must be specified to determine the highlighting rules.

    Example:
        .. code-block:: python

            from wildewidgets import CodeWidget

            python_code = '''
            def hello_world():
                print("Hello, world!")
            '''

            code_widget = CodeWidget(
                code=python_code,
                language="python",
                line_numbers=True
            )

    Note:
        Requires the `pygments` package to be installed.

    Args:
        code: The code to be displayed
        language: The programming language for syntax highlighting
        line_numbers: Whether to display line numbers
        **kwargs: Additional arguments passed to the parent class

    Raises:
        ValueError: If no language is specified
        RuntimeError: If Pygments is not installed

    """

    #: The name of the block for CSS styling
    block: str = "wildewidgets_highlight_container"

    #: The code to be displayed
    code: str = ""
    #: The programming language for the :py:attr:`code`
    language: str | None = None
    #: If ``True``, show line numbers
    line_numbers: bool = False

    def __init__(
        self,
        code: str | None = None,
        language: str | None = None,
        line_numbers: bool = False,
        **kwargs: Any,
    ):
        # Raise RuntimeError if pygments is not installed
        if not (get_lexer_by_name and highlight and HtmlFormatter):
            msg = "Pygments is not installed. Please install it to use CodeWidget."
            raise RuntimeError(msg)
        self.code = code if code else self.code
        self.language = language if language else self.language
        if not self.language:
            msg = (
                f'{self.__class__.__name__}: "language" must be defined either as a '
                "class attribute or a keyword arg"
            )
            raise ValueError(msg)
        self.line_numbers = line_numbers if line_numbers else self.line_numbers
        super().__init__(**kwargs)
        self.add_code(self.code, language=self.language, line_numbers=self.line_numbers)

    def add_code(self, code: str, language: str, line_numbers: bool = False) -> None:
        """
        Apply syntax highlighting to code and add it to the widget.

        Args:
            code: The code to highlight
            language: The programming language to use for highlighting
            line_numbers: Whether to display line numbers

        """
        lexer = get_lexer_by_name(language)
        formatter = HtmlFormatter(
            linenos=line_numbers, cssclass="wildewidgets_highlight"
        )
        self.add_block(highlight(code, lexer, formatter))


class MarkdownWidget(TemplateWidget):
    """
    A widget that renders Markdown text as HTML.

    This widget converts Markdown formatted text to HTML and displays it.
    It requires Django's template system to render the HTML.

    Attributes:
        template_name: The Django template used to render the widget
        text: The Markdown text to render
        css_class: CSS classes to apply to the container

    Example:
        .. code-block:: python

            from wildewidgets import MarkdownWidget

            markdown_text = '''
            # Hello World

            This is a **bold** statement with *emphasis*.

            - Item 1
            - Item 2
            '''

            widget = MarkdownWidget(text=markdown_text, css_class="my-markdown")

    Args:
        *args: Positional arguments passed to the parent class

    Keyword Args:
        **kwargs: Keyword arguments including:
            text: The Markdown text to render
            css_class: CSS classes to apply to the container

    """

    template_name = "wildewidgets/markdown_widget.html"
    text: str = ""
    css_class: str = ""

    def __init__(self, *args: Any, **kwargs: Any):
        self.text = kwargs.pop("text", self.text)
        self.css_class = kwargs.pop("css_class", self.css_class)
        super().__init__(*args, **kwargs)

    def get_context_data(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """
        Prepare the context data for template rendering.

        Args:
            *args: Positional arguments passed to the parent method
            **kwargs: Keyword arguments passed to the parent method

        Returns:
            dict: The context dictionary with markdown text and CSS classes

        """
        kwargs = super().get_context_data(*args, **kwargs)
        kwargs["text"] = self.text
        kwargs["css_class"] = self.css_class
        return kwargs


class HTMLWidget(TemplateWidget):
    """
    A widget that renders raw HTML content.

    This widget allows for displaying arbitrary HTML content within
    your Django application. Use with caution as it can introduce
    security risks if displaying user-provided content.

    Attributes:
        template_name: The Django template used to render the widget
        html: The raw HTML content to display
        css_class: CSS classes to apply to the container

    Example:
        .. code-block:: python

            from wildewidgets import HTMLWidget

            html_content = '<p>This is <strong>HTML</strong> content</p>'
            widget = HTMLWidget(html=html_content, css_class="custom-html-block")

    Warning:
        Be careful when using this widget with user-provided content as it
        could lead to cross-site scripting (XSS) vulnerabilities.

    Args:
        *args: Positional arguments passed to the parent class

    Keyword Args:
        **kwargs: Keyword arguments including:
            html: The raw HTML content to display
            css_class: CSS classes to apply to the container

    """

    template_name = "wildewidgets/html_widget.html"
    html: str = ""
    css_class: str | None = None

    def __init__(self, *args: Any, **kwargs: Any):
        self.html = kwargs.pop("html", self.html)
        self.css_class = kwargs.pop("css_class", self.css_class)
        super().__init__(*args, **kwargs)

    def get_context_data(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """
        Prepare the context data for template rendering.

        Args:
            *args: Positional arguments passed to the parent method
            **kwargs: Keyword arguments passed to the parent method

        Returns:
            dict: The context dictionary with HTML content and CSS classes

        """
        kwargs = super().get_context_data(*args, **kwargs)
        kwargs["html"] = self.html
        kwargs["css_class"] = self.css_class
        return kwargs


class StringBlock(Block):
    """
    A basic widget that displays a string.

    This is a simple wrapper around Block that initializes with a text string.

    .. deprecated:: 0.14.0
        Use :py:class:`wildewidgets.Block` directly instead.
        It works exactly like :py:class:`StringBlock`

    Args:
        text: The text to display
        **kwargs: Additional arguments passed to the parent class

    Example:
        .. code-block:: python

            # Deprecated usage
            from wildewidgets import StringBlock

            text_block = StringBlock("Hello, world!")

            # Preferred usage
            from wildewidgets import Block

            text_block = Block("Hello, world!")

    Args:
        text: The text to display

    Keyword Args:
        **kwargs: Additional arguments passed to the parent class

    """

    def __init__(self, text: str, **kwargs: Any):
        warnings.warn(
            "Deprecated in 0.14.0; use Block directly instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*[text], **kwargs)


class TimeStamp(Block):
    """
    A widget that displays text formatted as a timestamp.

    This widget renders text in a small font with light styling,
    making it suitable for timestamps, captions, or other secondary text.

    Attributes:
        tag: HTML tag to use for the timestamp (small)
        css_class: CSS class for styling the timestamp

    Example:
        .. code-block:: python

            from wildewidgets import TimeStamp

            timestamp = TimeStamp("Last updated: 2023-06-15 14:30")

    """

    tag = "small"
    css_class = "fw-light"


class TagBlock(Block):
    """
    A widget that displays text as a colored badge/tag.

    This widget creates a Bootstrap badge with customizable color,
    useful for status indicators, categories, or other labeled items.

    Example:
        .. code-block:: python

            from wildewidgets import TagBlock

            # Creates a success (green) badge
            status_tag = TagBlock("Active", color="success")

            # Creates a danger (red) badge
            error_tag = TagBlock("Error", color="danger")

            # Creates a custom colored badge
            custom_tag = TagBlock("Custom", color="info")

    Note:
        The color parameter accepts standard Bootstrap color names like
        "primary", "secondary", "success", "danger", "warning", "info", etc.

    Args:
        text: The text to display in the badge

    Keyword Args:
        color: The Bootstrap color class to use (default: "secondary")
        **kwargs: Additional arguments passed to the parent class


    """

    block: str = "badge"

    def __init__(self, text: str, color: str = "secondary", **kwargs: Any):
        super().__init__(text, **kwargs)
        self.add_class(f"bg-{color}")
