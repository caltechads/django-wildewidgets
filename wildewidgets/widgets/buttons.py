from __future__ import annotations

from copy import copy
from typing import Any

from .base import Block


class Button(Block):
    """
    Render a ``<button>`` with Bootstrap styling.

    Example:

        .. code-block:: python

            from wildewidgets import Button

            button = Button(text="My Button")

        When rendered in the template with the ``wildewdigets`` template tag, this
        will produce:

        .. code-block:: html

            <button type="button" class="button btn btn-secondary">My Button</button>

    Keyword Args:
        text: The text to use for the button
        color: The Boostrap color class to use for the button
        close: The Boostrap close icon will be used for the button
        size: The Bootstrap button size - None, 'sm', 'lg'
        disabled: If ``True``, the button will be disabled

    """

    block: str = "button"
    tag: str = "button"

    #: The Boostrap color class to use for the button
    color: str = "secondary"
    #: The text to use for the button
    text: str = "Button"
    #: If ``True``, ignore :py:attr:`text` and make this into a Bootstrap
    #: "close" button with a close icon.
    close: bool = False
    #: If ``True``, ignore :py:attr:`text` and make this into a Bootstrap
    #: "close" button with a close icon.
    size: str | None = None
    disabled: bool = False

    def __init__(
        self,
        text: str | None = None,
        color: str | None = None,
        close: bool | None = None,
        size: str | None = None,
        disabled: bool | None = None,
        **kwargs: Any,
    ) -> None:
        self.color = color if color is not None else self.color
        self.text = text if text is not None else self.text
        self.close = close if close is not None else self.close
        self.size = size if size is not None else self.size
        self.disabled = disabled if disabled is not None else self.disabled
        if self.disabled:
            if "attributes" in kwargs:
                kwargs["attributes"]["disabled"] = True
            else:
                kwargs["attributes"] = {"disabled": True}
        if self.close:
            self.text = ""
        super().__init__(self.text, **kwargs)
        self._attributes["type"] = "button"
        if self.close:
            self.add_class("btn-close")
            self._aria_attributes["label"] = "Close"
        else:
            self.add_class("btn")
            self.add_class(f"btn-{self.color}")
            if self.size:
                self.add_class(f"btn-{self.size}")


class ModalButton(Button):
    """
    Render a ``<button>`` with Bootstrap styling which toggles a Bootstrap modal.

    Example:

        .. code-block:: python

            from wildewidgets import ModalButton

            button = ModalButton(text="My Button", target='#mymodal')

        When rendered in the template with the ``wildewdigets`` template tag, this
        will produce:

        .. code-block:: html

            <button type="button" class="button button--modal btn btn-secondary"
            data-toggle="modal" data-target="#mymodal">My Button</button>

    Keyword Args:
        target: The CSS target for the Bootstrap modal

    """

    block: str = "button button--modal"

    #: The CSS target for the Bootstrap modal
    target: str | None = None

    def __init__(self, target: str | None = None, **kwargs: Any) -> None:
        self.target = target if target else self.target
        assert self.target is not None, "ModalButton requires a target"  # noqa: S101
        super().__init__(**kwargs)
        self._data_attributes["toggle"] = "modal"
        self._data_attributes["target"] = self.target


class CollapseButton(Button):
    """
    Render a ``<button>`` with Bootstrap styling which toggles a ``collapse``.

    Example:
        ... code-block:: python

            from wildewidgets import CollapseButton

            button = CollapseButton(text="My Button", target='#mymodal')

        When rendered in the template with the ``wildewdigets`` template tag, this
        will produce:

        ... code-block:: html

            <button type="button" class="button button--collapse btn btn-secondary"
                data-toggle="collapse" data-target="#mymodal"
                aria-expanded="false" aria-controls="mymodal">My Button</button>

    Keyword Args:
        target: The CSS target for the Bootstrap collapse

    """

    block: str = "button button--collapse"

    #: The CSS target for the Bootstrap collapse
    target: str | None = None

    def __init__(self, target: str | None = None, **kwargs: Any) -> None:
        self.target = target if target else self.target
        assert self.target is not None, "CollapseButton requires a target"  # noqa: S101
        super().__init__(**kwargs)
        self._data_attributes["toggle"] = "collapse"
        self._data_attributes["target"] = self.target
        self._aria_attributes["expanded"] = "false"
        self._aria_attributes["controls"] = self.target.lstrip("#")


class LinkButton(Button):
    """
    Render an ``<a>`` with Bootstrap button styling which toggles a Bootstrap
    modal.

    Example:
        ... code-block:: python

            from wildewidgets import LinkButton

            button = LinkButton(text="My Button", url='https://myexample.com')

        When rendered in the template with the ``wildewdigets`` template tag, this
        will produce:

        ... code-block:: html

            <a href="https://myexample.com"
                class="button button--link btn btn-secondary">
                My Button
            </a>


    Keyword Args:
        url: The URL for the ``href`` attribute of the <a> record, defaults to no URL.

    """

    block: str = "button button--link"
    tag: str = "a"

    url: str | None = None

    def __init__(self, url: str | None = None, **kwargs: Any) -> None:
        self.url = url if url else self.url
        assert self.url is not None, "LinkButton requires a url"  # noqa: S101
        super().__init__(**kwargs)
        del self._attributes["type"]
        if url:
            self._attributes["href"] = self.url


class InputButton(Button):
    """
    Render an ``<input type="submit">`` with Bootstrap button styling.

    Example::

        .. code-block:: python

            from wildewidgets import InputButton

            button = InputButton(text="Save")

        When rendered in the template with the ``wildewdigets`` template tag, this
        will produce:

        .. code-block:: html

            <input type="submit"
                class="button button--submit btn btn-secondary" value="Save">

    """

    template_name: str = "wildewidgets/block--simple.html"

    block: str = "button--submit"
    tag: str = "input"

    confirm_text: str | None = None

    def __init__(self, confirm_text: str | None = None, **kwargs: Any) -> None:
        self.confirm_text = confirm_text if confirm_text else self.confirm_text
        super().__init__(**kwargs)
        self._attributes["type"] = "submit"
        self._attributes["value"] = self.text
        if self.confirm_text:
            self._attributes["onclick"] = f"return confirm('{self.confirm_text}');"
        self.text = ""


class FormButton(Block):
    """
    Render a ``<form>`` with optional hidden inputs and a submit button.

    Example::

        .. code-block:: python

            from wildewidgets import FormButton

            button = FormButton(
                text="Save",
                action='/my/form/action',
                data={'field1': 'value1'}
            )

        When rendered in the template with the ``wildewdigets`` template tag, this
        will produce:

        .. code-block:: html

            <form action="/my/form/action" method="post" class="button-form">
                <input type="hidden" name="csrfmiddlewaretoken"
                    value="__THE_CSRF_TOKEN__">
                <input type="hidden" name="field1" value="value1">
                <input type="submit" class="button button--submit btn btn-secondary"
                    value="Save">
            </form>

    All the constructor parameters can be set in a subclass of this class as
    class attributes.  Parameters to the constructor override any defined class
    attributes.

    Keyword Args:
        text: The text to use for the button, defaults to 'Button'
        color: The Boostrap color class to use for the button, defaults to 'secondary'
        button_css_class: a string of classes to apply to the button, defaults
            to no classes.
        button_attributes: Set any additional attributes for the button as key,
            value pairs, defaults to no additional attributes.
        button_data_attributes: Set ``data-`` attributes for the button, defaults to no
            data attributes

    """

    template_name: str = "wildewidgets/button--form.html"
    tag: str = "form"
    block: str = "button-form"

    action: str | None = None
    method: str = "post"
    text: str | None = None
    color: str = "secondary"
    button_css_class: str | None = None
    button_attributes: dict[str, str] = {}  # noqa: RUF012
    button_data_attributes: dict[str, str] = {}  # noqa: RUF012
    confirm_text: str | None = None
    data: dict[str, Any] = {}  # noqa: RUF012

    def __init__(self, **kwargs: Any) -> None:
        action = kwargs.pop("action", self.action)
        method = kwargs.pop("method", self.method)
        self.close = kwargs.pop("close", False)
        self.data = kwargs.pop("data", copy(self.data))
        self.button = self.__build_button(kwargs)
        super().__init__(**kwargs)
        self._attributes["method"] = method
        self._attributes["action"] = action

    def __build_button(self, kwargs: dict[str, Any]) -> InputButton:
        """
        Build the submit button for the form.

        Creates an InputButton with appropriate styling and attributes based on
        the configuration provided to the FormButton.

        Args:
            kwargs: Dictionary of keyword arguments to process

        Returns:
            InputButton: The configured submit button for the form

        """
        button_kwargs = {
            "text": kwargs.pop("text", self.text),
            "color": kwargs.pop("color", self.color),
            "css_class": kwargs.pop("button_css_class", self.button_css_class),
            "attributes": kwargs.pop("button_attributes", copy(self.button_attributes)),
            "data_attributes": kwargs.pop(
                "button_data_attributes", copy(self.button_data_attributes)
            ),
        }
        if self.close:
            button_kwargs["close"] = True
            button_kwargs["aria_attributes"] = {"label": "Close"}
        button_kwargs["confirm_text"] = kwargs.pop("confirm_text", self.confirm_text)
        return InputButton(**button_kwargs)

    def get_context_data(self, *args, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(*args, **kwargs)
        context["button"] = self.button
        context["data"] = self.data
        return context


class ButtonRow(Block):
    """
    Renders a row of buttons with right alignment.

    This class creates a horizontal row of buttons with right-aligned (end)
    justification using Bootstrap's flexbox utilities. It's useful for placing
    action buttons at the bottom of forms or dialogs.

    Note:
        This class is planned for deprecation in favor of
        :py:class:`HorizontalLayoutBlock`.

    Example:
        .. code-block:: python

            from wildewidgets import Button, ButtonRow

            save_button = Button(text="Save", color="primary")
            cancel_button = Button(text="Cancel")
            button_row = ButtonRow(save_button, cancel_button)

        When rendered, this produces:

        .. code-block:: html

            <div class="d-flex justify-content-end">
                <button type="button" class="button btn btn-primary">Save</button>
                <button type="button" class="button btn btn-secondary">Cancel</button>
            </div>

    Args:
        *blocks: Button instances or other blocks to include in the row

    Keyword Args:
        **kwargs: Additional keyword arguments passed to the parent Block class

    """

    def __init__(self, *blocks: Any, **kwargs: Any) -> None:
        """
        Initialize a ButtonRow with buttons and styling.

        Adds flexbox utility classes to create a right-aligned row of buttons.

        Args:
            *blocks: Button instances or other blocks to include in the row
            **kwargs: Additional keyword arguments including css_class

        """
        css_class = kwargs.get("css_class", "")
        css_class += " d-flex justify-content-end"
        kwargs["css_class"] = css_class
        super().__init__(*blocks, **kwargs)
