from __future__ import annotations

from typing import Any

from .base import Block, Image, TemplateWidget
from .structure import HorizontalLayoutBlock
from .text import CodeWidget


class KeyValueListBlock(Block):
    """
    A list that displays key-value pairs.

    This widget creates a Bootstrap list group to display key-value pairs.
    Each pair is rendered as a list item with the key and value positioned
    horizontally. The values can be simple text or code blocks with syntax
    highlighting.

    Example:
        .. code-block:: python

            from wildewidgets import KeyValueListBlock

            # Create a key-value list
            kv_list = KeyValueListBlock()

            # Add simple text pairs
            kv_list.add_simple_key_value("Name:", "John Doe")
            kv_list.add_simple_key_value("Email:", "john@example.com")

            # Add a code value with syntax highlighting
            kv_list.add_code_key_value(
                "JSON Response:",
                '{"status": "success", "data": {"id": 123}}',
                language="json"
            )

    """

    #: The HTML tag to use for the container
    tag: str = "ul"
    #: The CSS class for the container
    block: str = "list-group"

    def add_simple_key_value(self, key: Any, value: Any) -> None:
        """
        Add a simple key-value pair to the list.

        Creates a list item containing the key and value positioned horizontally.
        Both key and value are rendered as simple text.

        Args:
            key: The label or key to display (left side)
            value: The value to display (right side)

        """
        self.add_block(
            HorizontalLayoutBlock(
                Block(key),
                Block(value),
                tag="li",
                css_class="list-group-item",
            )
        )

    def add_code_key_value(
        self, key: Any, value: Any, language: str | None = None
    ) -> None:
        """
        Add a key-value pair with syntax-highlighted code as the value.

        Creates a list item containing the key and a code block for the value.
        The code block can have syntax highlighting for a specific language.

        Args:
            key: The label or key to display
            value: The code to display in the code block

        Keyword Args:
            language: Optional language identifier for syntax highlighting

        """
        self.add_block(
            Block(
                Block(key),
                CodeWidget(
                    code=value,
                    language=language,
                    css_class="m-3",
                ),
                tag="li",
                css_class="list-group-item",
            )
        )


class GravatarWidget(Image):
    """
    Display a Gravatar profile picture as a circular image.

    This widget creates a circular image that displays a user's Gravatar profile
    picture. It automatically sets the appropriate styling for a responsive,
    rounded avatar image.

    Example:
        .. code-block:: python

            from wildewidgets import GravatarWidget

            # Create a standard-sized Gravatar
            gravatar = GravatarWidget(
                gravatar_url="https://www.gravatar.com/avatar/hash",
                fullname="John Doe"
            )

            # Create a larger Gravatar
            large_gravatar = GravatarWidget(
                gravatar_url="https://www.gravatar.com/avatar/hash",
                size=64,
                fullname="Jane Smith"
            )

    """

    block: str = "rounded-circle"

    #: The gravatar URL
    gravatar_url: str | None = None
    #: The length in pixels that will used as the height and width of the image
    size: int | str = 28
    #: The person's name.  This will be used as the ``alt`` tag on the image
    fullname: str | None = None

    def __init__(
        self,
        gravatar_url: str | None = None,
        size: int | str | None = None,
        fullname: str | None = None,
        **kwargs: Any,
    ):
        """
        Initialize a Gravatar widget with specified settings.

        Creates a circular image that displays a Gravatar profile picture.

        Args:
            gravatar_url: URL to the Gravatar image
            size: Size of the Gravatar image in pixels (both width and height)
            fullname: Person's name to use as alt text for accessibility
            **kwargs: Additional arguments to pass to the parent Image class

        Raises:
            ValueError: If the size parameter cannot be converted to an integer

        """
        self.gravatar_url = (
            gravatar_url if gravatar_url is not None else self.gravatar_url
        )
        self.size = size if size is not None else self.size
        self.fullname = fullname if fullname is not None else self.fullname
        try:
            int(self.size)
        except ValueError as e:
            msg = f'size should be an integer; got "{self.size}" instead'
            raise ValueError(msg) from e
        kwargs["src"] = self.gravatar_url
        if self.fullname:
            kwargs["alt"] = self.fullname
        super().__init__(**kwargs)
        self._attributes["style"] = f"width: {self.size}px; height: {self.size}px"


class InitialsAvatarWidget(TemplateWidget):
    """
    Display a person's initials in a colored circle.

    This widget creates an SVG-based avatar showing a person's initials
    in a colored circle, similar to those used in many applications when
    a profile picture is not available.

    Example:
        .. code-block:: python

            from wildewidgets import InitialsAvatarWidget

            # Create an avatar with default sizing and colors
            avatar = InitialsAvatarWidget(initials="JD", fullname="John Doe")

            # Create a larger avatar with custom colors
            custom_avatar = InitialsAvatarWidget(
                initials="AB",
                size=48,
                color="#ffffff",
                background_color="#336699",
                fullname="Alice Brown"
            )

    """

    #: The path to the template used to render this widget
    template_name: str = "wildewidgets/initials_avatar.html"

    #: The length in pixels that will used as the height and width of the gravatar
    size: int = 28
    #: The foreground color for the gravatar
    color: str = "white"
    #: The background color for the gravatar
    background_color: str = "#626976"

    def __init__(
        self,
        *args: Any,
        initials: str | None = None,
        size: int | None = None,
        color: str | None = None,
        background_color: str | None = None,
        fullname: str | None = None,
        **kwargs: Any,
    ):
        """
        Initialize an initials avatar widget.

        Args:
            *args: Positional arguments passed to parent class, typically not used,
                but can be used to insert additional blocks

        Keyword Args:
            initials: The initials to display in the avatar (typically 1-3 characters)
            size: Size of the avatar in pixels (both width and height)
            color: Text color for the initials (CSS color string)
            background_color: Background color for the circle (CSS color string)
            fullname: Person's full name for accessibility
            **kwargs: Additional keyword arguments passed to parent class

        """
        assert initials, (  # noqa: S101
            "initials must be defined as a keyword argument"
        )
        self.initials = initials
        self.size = size or self.size
        self.color = color or self.color
        self.background_color = background_color or self.background_color
        self.fullname = fullname
        super().__init__(*args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Prepare the context data for template rendering.

        Processes the widget parameters and adds them to the template context
        for rendering the SVG avatar.

        Args:
            **kwargs: Initial context dictionary

        Returns:
            dict: Updated context dictionary with avatar properties

        Note:
            The method converts initials to uppercase and calculates the
            half-size value needed for SVG centering.

        """
        kwargs = super().get_context_data(**kwargs)
        kwargs["initials"] = self.initials.upper()
        kwargs["fullsize"] = str(self.size)
        kwargs["halfsize"] = str(self.size / 2)
        kwargs["color"] = self.color
        kwargs["background_color"] = self.background_color
        kwargs["fullname"] = self.fullname
        return kwargs
