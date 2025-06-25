from __future__ import annotations

import warnings
from typing import Any

from .base import Block, TemplateWidget
from .buttons import CollapseButton, FormButton, LinkButton, ModalButton


class BasicHeader(TemplateWidget):
    """
    The base header class for all header widgets in the wildewidgets library.

    This class provides the core functionality for rendering HTML headers with
    various styling options, including optional badges. All other header classes
    inherit from this class.

    Example:
        .. code-block:: python

            from wildewidgets import BasicHeader

            header = BasicHeader(
                header_text="Welcome to the Dashboard",
                header_level=1,
                badge_text="New",
                badge_class="success"
            )

    Attributes:
        template_name: Path to the Django template used for rendering
        header_level: HTML heading level (1-6) to use
        header_type: Type of header styling ("h" for standard, "display" for larger)
        header_text: The text content of the header
        css_class: CSS classes to apply to the header container
        css_id: Optional ID attribute for the header element
        badge_text: Optional text for a badge beside the header
        badge_class: Bootstrap color class for the badge (e.g., "primary",
            "warning")
        badge_rounded_pill: Whether to style the badge as a rounded pill

    Keyword Args:
        header_level: the header depth, as in h1, h2, h3...
        header_type: the Boostrap 5 header class, either h-*, or display-*.
        header_text: the text of the header.
        css_class: any css classes to apply to the header.
        css_id: an ID to add to the header div.
        badge_text: text to add in a badge to the right of the main header text.
        badge_class: the css class to add to the badge.

    """

    template_name: str = "wildewidgets/header_with_controls.html"

    header_level: int = 1
    header_type: str = "h"
    header_text: str | None = None
    css_class: str = "my-3"
    css_id: str | None = None
    badge_text: str | None = None
    badge_class: str = "warning"
    badge_rounded_pill: bool = True

    def __init__(
        self,
        header_level: int | None = None,
        header_type: str | None = None,
        header_text: str | None = None,
        css_class: str | None = None,
        css_id: str | None = None,
        badge_text: str | None = None,
        badge_class: str | None = None,
        badge_rounded_pill: bool | None = None,
        **kwargs: Any,
    ):
        self.header_level = header_level if header_level else self.header_level
        self.header_type = header_type if header_type else self.header_type
        self.header_text = header_text if header_text else self.header_text
        self.css_class = css_class if css_class else self.css_class
        self.css_id = css_id if css_id else self.css_id
        self.badge_text = badge_text if badge_text else self.badge_text
        self.badge_class = badge_class if badge_class else self.badge_class
        self.badge_rounded_pill = (
            badge_rounded_pill
            if badge_rounded_pill is not None
            else self.badge_rounded_pill
        )
        kwargs["title"] = self.header_text
        super().__init__(**kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Prepare the context data for template rendering.

        Processes header settings and adds them to the template context.
        Sets the appropriate header class based on the header type and level,
        and includes all other header properties.

        Args:
            **kwargs: Initial context dictionary

        Returns:
            dict: Updated context dictionary with header properties

        """
        if self.header_type == "h":
            kwargs["header_class"] = f"h{self.header_level}"
        elif self.header_type == "display":
            kwargs["header_class"] = f"display-{self.header_level}"

        kwargs["header_level"] = self.header_level
        kwargs["header_text"] = self.header_text
        kwargs["header_type"] = self.header_type
        kwargs["css_class"] = self.css_class
        kwargs["css_id"] = self.css_id
        kwargs["badge_text"] = self.badge_text
        kwargs["badge_class"] = self.badge_class
        kwargs["badge_rounded_pill"] = self.badge_rounded_pill
        return kwargs


class HeaderWithLinkButton(BasicHeader):
    """
    A header with an attached link button.

    This combines a heading element with a button that links to a specified URL.
    The button appears to the right of the header text.

    Deprecated:
        This class is deprecated since version 0.13.45.
        Use :py:class:`HeaderWithWidget` with the :py:meth:`add_link_button`
        method instead.

    Example:
        .. code-block:: python

            from wildewidgets import HeaderWithLinkButton

            header = HeaderWithLinkButton(
                header_text="Users",
                header_level=2,
                url="/users/add/",
                link_text="Add User",
                button_class="success"
            )

    Attributes:
        template_name: Path to the template for rendering this widget
        url: The URL that the button links to
        link_text: The text displayed on the button
        button_class: Bootstrap contextual class for the button

    """

    template_name = "wildewidgets/header_with_link_button.html"

    url: str | None = None
    link_text: str | None = None
    button_class: str = "primary"

    def __init__(
        self,
        url: str | None = None,
        link_text: str | None = None,
        button_class: str | None = None,
        **kwargs: Any,
    ):
        warnings.warn(
            "HeaderWithLinkButton is deprecated. Use "
            "wildewidgets.HeaderWithWidget instead",
            DeprecationWarning,
            stacklevel=2,
        )
        self.url = url if url else self.url
        self.link_text = link_text if link_text else self.link_text
        self.button_class = button_class if button_class else self.button_class
        super().__init__(**kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Prepare the context data for template rendering.

        Adds link button specific variables to the context dictionary.

        Args:
            **kwargs: Initial context dictionary from parent class

        Returns:
            dict: Updated context with url, link_text, and button_class

        """
        kwargs = super().get_context_data(**kwargs)
        kwargs["url"] = self.url
        kwargs["link_text"] = self.link_text
        kwargs["button_class"] = self.button_class
        return kwargs


class HeaderWithFormButton(BasicHeader):
    """
    A header with an attached form submission button.

    This combines a heading element with a button that submits a form
    when clicked. The form must be defined elsewhere in your template.

    Deprecated:
        This class is deprecated since version 0.13.45.
        Use :py:class:`HeaderWithWidget` with the :py:meth:`add_form_button`
        method instead.

    Example:
        .. code-block:: python

            from wildewidgets import HeaderWithFormButton

            header = HeaderWithFormButton(
                header_text="Dangerous Action",
                header_level=3,
                url="/api/delete-all/",
                button_text="Delete All"
            )

    Attributes:
        template_name: Path to the template for rendering this widget
        url: The URL that the form will submit to
        button_text: The text displayed on the button

    """

    template_name = "wildewidgets/header_with_form_button.html"

    url: str | None = None
    button_text: str | None = None

    def __init__(
        self, url: str | None = None, button_text: str | None = None, **kwargs: Any
    ):
        warnings.warn(
            "HeaderWithFormButton is deprecated. Use "
            "wildewidgets.HeaderWithWidget instead",
            DeprecationWarning,
            stacklevel=2,
        )
        self.url = url if url else self.url
        self.button_text = button_text if button_text else self.button_text
        super().__init__(**kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Prepare the context data for template rendering.

        Adds form button specific variables to the context dictionary.

        Args:
            **kwargs: Initial context dictionary from parent class

        Returns:
            dict: Updated context with url and button_text

        """
        kwargs = super().get_context_data(**kwargs)
        kwargs["url"] = self.url
        kwargs["button_text"] = self.button_text
        return kwargs


class HeaderWithCollapseButton(BasicHeader):
    """
    A header with a button that toggles a Bootstrap collapsible element.

    This combines a heading element with a button that expands or collapses
    a target element when clicked. The collapsible element must be defined
    elsewhere in your template.

    Deprecated:
        This class is deprecated since version 0.13.45.
        Use :py:class:`HeaderWithWidget` with the :py:meth:`add_collapse_button`
        method instead.

    Example:
        .. code-block:: python

            from wildewidgets import HeaderWithCollapseButton

            header = HeaderWithCollapseButton(
                header_text="Advanced Options",
                header_level=3,
                collapse_id="advanced-options",
                button_text="Toggle"
            )

    Attributes:
        template_name: Path to the template for rendering this widget
        collapse_id: ID of the collapsible element to toggle
        button_text: Text displayed on the button
        button_class: Bootstrap contextual class for the button

    """

    template_name: str = "wildewidgets/header_with_collapse_button.html"

    collapse_id: str | None = None
    button_text: str | None = None
    button_class: str | None = "primary"

    def __init__(
        self,
        collapse_id: str | None = None,
        button_text: str | None = None,
        button_class: str | None = None,
        **kwargs: Any,
    ):
        warnings.warn(
            "HeaderWithCollapseButton is deprecated. Use "
            "wildewidgets.HeaderWithWidget instead",
            DeprecationWarning,
            stacklevel=2,
        )
        self.collapse_id = collapse_id if collapse_id else self.collapse_id
        self.button_text = button_text if button_text else self.button_text
        self.button_class = button_class if button_class else self.button_class
        super().__init__(**kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Prepare the context data for template rendering.

        Adds collapse button specific variables to the context dictionary.

        Args:
            **kwargs: Initial context dictionary from parent class

        Returns:
            dict: Updated context with collapse_id, button_text, and button_class

        """
        kwargs = super().get_context_data(**kwargs)
        kwargs["collapse_id"] = self.collapse_id
        kwargs["button_text"] = self.button_text
        kwargs["button_class"] = self.button_class
        return kwargs


class HeaderWithModalButton(BasicHeader):
    """
    A header widget with a button that triggers a Bootstrap modal.

    This class combines a heading element with a button that opens a modal dialog
    when clicked. The modal must be defined elsewhere in your template.

    Deprecated:
        This class is deprecated since version 0.13.45.
        Use :py:class:`HeaderWithWidget` with the :py:meth:`add_modal_button`

    Attributes:
        template_name: Path to the template for rendering this widget
        modal_id: ID of the modal to be triggered by the button
        button_text: Text to display on the button
        button_class: Bootstrap button class (e.g., "primary", "secondary")

    Keyword Args:
        **kwargs: Keyword arguments including modal_id, button_text, and
            button_class, plus any arguments for BasicHeader

    """

    template_name = "wildewidgets/header_with_modal_button.html"
    modal_id: str | None = None
    button_text: str | None = None
    button_class: str = "primary"

    def __init__(self, **kwargs: Any):
        warnings.warn(
            "Use wildewidgets.HeaderWithWidget instead",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**kwargs)
        self.modal_id = kwargs.get("modal_id", self.modal_id)
        self.button_text = kwargs.get("button_text", self.button_text)
        self.button_class = kwargs.get("button_class", self.button_class)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Prepare the context data for template rendering.

        Adds modal button specific variables to the context dictionary.

        Args:
            **kwargs: Initial context dictionary from parent class

        Returns:
            dict: Updated context with modal_id, button_text, and button_class

        """
        kwargs = super().get_context_data(**kwargs)
        kwargs["modal_id"] = self.modal_id
        kwargs["button_text"] = self.button_text
        kwargs["button_class"] = self.button_class
        return kwargs


class HeaderWithWidget(BasicHeader):
    """
    A header widget that can contain another widget (typically a button).

    This flexible header class allows adding any widget (most commonly buttons)
    next to the header text. This is the recommended approach for creating headers
    with interactive elements.

    Example:
        .. code-block:: python

            from wildewidgets import HeaderWithWidget, LinkButton

            # Create a header with a link button
            header = HeaderWithWidget(
                header_text="Products List",
                header_level=2,
                widget=LinkButton(text="Add Product", url="/products/add/")
            )

            # Or add the button after initialization
            header = HeaderWithWidget(header_text="Products List")
            header.add_link_button(text="Add Product", url="/products/add/")

    Args:
        widget: Widget to display next to the header text

    Keyword Args:
        header_text: Text content of the header
        header_level: HTML heading level (1-6)
        **kwargs: Additional arguments passed to BasicHeader

    """

    template_name = "wildewidgets/header_with_widget.html"

    def __init__(self, widget: Block | None = None, **kwargs: Any):
        super().__init__(**kwargs)
        self.widget = widget

    def add_form_button(self, **kwargs: Any) -> None:
        """
        Add a form submission button to the header.

        This method creates a FormButton instance and adds it to the header.
        The button will submit a form when clicked.

        Args:
            **kwargs: Arguments passed to :py:class:`wildewidgets.FormButton`
             constructor.
                Common arguments include:

                * text: Button label text
                * action: Form submission URL
                * color: Bootstrap color class (default: "secondary")
                * method: HTTP method (default: "post")
                * confirm_text: Text for confirmation dialog (if needed)

        """
        self.widget = FormButton(**kwargs)

    def add_link_button(self, **kwargs: Any) -> None:
        """
        Add a hyperlink button to the header.

        This method creates a LinkButton instance and adds it to the header.
        The button will navigate to the specified URL when clicked.

        Args:
            **kwargs: Arguments passed to :py:class:`wildewidgets.LinkButton`
                constructor.
                Common arguments include:

                * text: Button label text
                * url: Target URL for the link
                * color: Bootstrap color class (default: "secondary")
                * css_class: Additional CSS classes

        """
        self.widget = LinkButton(**kwargs)

    def add_modal_button(self, **kwargs: Any) -> None:
        """
        Add a button that triggers a Bootstrap modal dialog.

        This method creates a ModalButton instance and adds it to the header.
        The button will open the specified modal when clicked.

        Args:
            **kwargs: Arguments passed to :py:class:`wildewidgets.ModalButton`
                constructor.
                Common arguments include:

                * text: Button label text
                * target: Modal ID to target (with # prefix)
                * color: Bootstrap color class (default: "secondary")

        """
        self.widget = ModalButton(**kwargs)

    def add_collapse_button(self, **kwargs: Any) -> None:
        """
        Add a button that toggles a Bootstrap collapsible element.

        This method creates a CollapseButton instance and adds it to the header.
        The button will toggle the visibility of the specified collapsible element.

        Args:
            **kwargs: Arguments passed to
                :py:class:`wildewidgets.CollapseButton` constructor.
                Common arguments include:

                * text: Button label text
                * target: Collapse target ID (with # prefix)
                * color: Bootstrap color class (default: "secondary")

        """
        self.widget = CollapseButton(**kwargs)

    def set_widget(self, widget: Block) -> None:
        """
        Set or replace the widget displayed next to the header.

        This method allows setting any widget (not just buttons) to appear next
        to the header text. This provides flexibility beyond the specialized
        button methods.

        Args:
            widget: Any Block-derived widget to display in the header

        """
        self.widget = widget

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Get the context data for rendering the template.

        Adds the widget to the template context, along with other header properties.

        Args:
            **kwargs: Additional context variables

        Returns:
            dict: Updated context dictionary including the widget

        """
        kwargs = super().get_context_data(**kwargs)
        kwargs["widget"] = self.widget
        return kwargs


class PageHeader(HeaderWithWidget):
    """
    Provides a standard page header.

    This is an H1 header with a widget, typically used at the top of a page
    to provide a title and an action button or other interactive element.

    Example:
        .. code-block:: python

            from wildewidgets import PageHeader, LinkButton

            header = PageHeader(
                header_text="Welcome to the Dashboard",
                widget=LinkButton(text="Learn More", url="/about/")
            )

    """

    css_class: str = "my-4"


class CardHeader(HeaderWithWidget):
    """
    A header specifically designed for Bootstrap card components.

    This provides an H2 header with appropriate styling for use as a card header,
    with the option to include an action button or other widget.

    Example:
        .. code-block:: python

            from wildewidgets import CardHeader, LinkButton

            header = CardHeader(
                header_text="User Details",
                widget=LinkButton(text="Edit", url="/users/123/edit/")
            )

    """

    css_class: str = "my-3"
    header_level: int = 2


class WidgetListLayoutHeader(HeaderWithWidget):
    """
    A specialized header for use with WidgetListLayout components.

    This header is designed to match the styling of the WidgetListLayout
    component, providing consistent margins and header size. It can include
    an optional action button or other widget.

    Example:
        .. code-block:: python

            from wildewidgets import WidgetListLayoutHeader, LinkButton

            header = WidgetListLayoutHeader(
                header_text="Dashboard Widgets",
                widget=LinkButton(text="Add Widget", url="/widgets/add/")
            )

    """

    css_class: str = "mb-4"
    header_level: int = 2
