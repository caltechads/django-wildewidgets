#!/usr/bin/env python
# -*- coding: utf-8 -*-

from copy import copy
from typing import Dict, Any, Optional

from .base import Block


class Button(Block):
    """
    Render a ``<button>`` with Bootstrap styling.

    Example:

        >>> button = Button(text="My Button")

        When rendered in the template with the ``wildewdigets`` template tag, this
        will produce::

            <button type="button" class="button btn btn-secondary">My Button</button>

    Keyword Args:
        text: The text to use for the button
        color: The Boostrap color class to use for the button
        close: The Boostrap close icon will be used for the button
        size: The Bootstrap button size - None, 'sm', 'lg'
        disabled: If ``True``, the button will be disabled
    """
    block: str = 'button'
    tag: str = 'button'

    #: The Boostrap color class to use for the button
    color: str = 'secondary'
    #: The text to use for the button
    text: str = 'Button'
    #: If ``True``, ignore :py:attr:`text` and make this into a Bootstrap
    #: "close" button with a close icon.
    close: bool = False
    #: If ``True``, ignore :py:attr:`text` and make this into a Bootstrap
    #: "close" button with a close icon.
    size: str = None
    disabled: bool = False

    def __init__(
        self,
        text: str = None,
        color: str = None,
        close: bool = None,
        size: str = None,
        disabled: bool = None,
        **kwargs
    ):
        self.color = color if color else self.color
        self.text = text if text else self.text
        self.close = close if close else self.close
        self.size = size if size else self.size
        self.disabled = disabled if disabled else self.disabled
        if self.disabled:
            if "attributes" in kwargs:
                kwargs["attributes"]["disabled"] = True
            else:
                kwargs["attributes"] = {"disabled": True}
        if self.close:
            self.text = ""
        super().__init__(self.text, **kwargs)
        self._attributes['type'] = 'button'
        if self.close:
            self.add_class('btn-close')
            self._aria_attributes['label'] = "Close"
        else:
            self.add_class('btn')
            self.add_class(f'btn-{self.color}')
            if self.size:
                self.add_class(f'btn-{self.size}')


class ModalButton(Button):
    """
    Render a ``<button>`` with Bootstrap styling which toggles a Bootstrap modal.

    Example:

        >>> button = ModalButton(text="My Button", target='#mymodal')

        When rendered in the template with the ``wildewdigets`` template tag, this
        will produce::

            <button type="button" class="button button--modal btn btn-secondary" data-toggle="modal"
            data-target="#mymodal">My Button</button>

    Keyword Args:
        target: The CSS target for the Bootstrap modal
    """
    block: str = 'button button--modal'

    #: The CSS target for the Bootstrap modal
    target: Optional[str] = None

    def __init__(
        self,
        target: str = None,
        **kwargs
    ):
        self.target = target if target else self.target
        super().__init__(**kwargs)
        self._data_attributes['toggle'] = 'modal'
        self._data_attributes['target'] = self.target


class CollapseButton(Button):
    """
    Render a ``<button>`` with Bootstrap styling which toggles a ``collapse``.

    Example:

        >>> button = CollapseButton(text="My Button", target='#mymodal')

        When rendered in the template with the ``wildewdigets`` template tag, this
        will produce::

            <button type="button" class="button button--collapse btn btn-secondary"
                data-toggle="collapse" data-target="#mymodal"
                aria-expanded="false aria-controls="mymodal">My Button</button>

    Keyword Args:
        target: The CSS target for the Bootstrap collapse
    """
    block: str = 'button button--collapse'

    #: The CSS target for the Bootstrap collapse
    target: Optional[str] = None

    def __init__(
        self,
        target: str = None,
        **kwargs
    ):
        self.target = target if target else self.target
        super().__init__(**kwargs)
        self._data_attributes['toggle'] = 'collapse'
        self._data_attributes['target'] = self.target
        self._aria_attributes['expanded'] = 'false'
        self._aria_attributes['controls'] = self.target.lstrip("#")


class LinkButton(Button):
    """
    Render an ``<a>`` with Bootstrap button styling which toggles a Bootstrap
    modal.

    Example:

        >>> button = LinkButton(text="My Button", url='https://myexample.com')

        When rendered in the template with the ``wildewdigets`` template tag, this
        will produce::

            <a href="https://myexample.com" class="button button--link btn btn-secondary">My Button</a>


    Keyword Args:
        url: The URL for the ``href`` attribute of the <a> record, defaults to no URL.
    """
    block: str = 'button button--link'
    tag: str = 'a'

    url: Optional[str] = None

    def __init__(self, url: str = None, **kwargs):
        self.url = url if url else self.url
        super().__init__(**kwargs)
        del self._attributes['type']
        if url:
            self._attributes['href'] = self.url


class InputButton(Button):
    """
    Render an ``<input type="submit">`` with Bootstrap button styling.

    Example::

        >>> button = InputButton(text="Save")

    When rendered in the template with the ``wildewdigets`` template tag, this
    will produce::

        <input type="submit" class="button button--submit btn btn-secondary" value="Save">

    """
    template_name: str = 'wildewidgets/block--simple.html'

    block: str = 'button--submit'
    tag: str = 'input'

    confirm_text: str = None

    def __init__(
        self,
        confirm_text: str = None,
        **kwargs
    ):
        self.confirm_text = confirm_text if confirm_text else self.confirm_text
        super().__init__(**kwargs)
        self._attributes['type'] = 'submit'
        self._attributes['value'] = self.text
        if self.confirm_text:
            self._attributes['onclick'] = f"return confirm('{self.confirm_text}');"
        self.text = None


class FormButton(Block):
    """
    Render a ``<form>`` with optional hidden inputs and a submit button.

    Example::

        >>> button = FormButton(
            text="Save",
            action='/my/form/action',
            data={'field1': 'value1'}
        )

    When rendered in the template with the ``wildewdigets`` template tag, this
    will produce::

        <form action="/my/form/action" method="post" class="button-form">
            <input type="hidden" name="csrfmiddlewaretoken" value="__THE_CSRF_TOKEN__">
            <input type="hidden" name="field1" value="value1">
            <input type="submit" class="button button--submit btn btn-secondary" value="Save">
        </form>

    All the constructor parameters can be set in a subclass of this class as class attributes.  Parameters
    to the constructor override any defined class attributes.

    Keyword Args:
        text: The text to use for the button, defaults to 'Button'
        color: The Boostrap color class to use for the button, defaults to 'secondary'
        button_css_class: a string of classes to apply to the button, defaults to no classes.
        button_attributes: Set any additional attributes for the button as key, value pairs,
             defaults to no additional attributes.
        button_data_attributes: Set ``data-`` attributes for the button, defaults to no
            data attributes
    """
    template_name: str = 'wildewidgets/button--form.html'
    tag: str = 'form'
    block: str = 'button-form'

    action: Optional[str] = None
    method: str = 'post'
    text: Optional[str] = None
    color: str = 'secondary'
    button_css_class: Optional[str] = None
    button_attributes: Dict[str, str] = {}
    button_data_attributes: Dict[str, str] = {}
    confirm_text: Optional[str] = None
    data: Dict[str, Any] = {}

    def __init__(self, **kwargs):
        action = kwargs.pop('action', self.action)
        method = kwargs.pop('method', self.method)
        self.close = kwargs.pop('close', False)
        self.data = kwargs.pop('data', copy(self.data))
        self.button = self.__build_button(kwargs)
        super().__init__(**kwargs)
        self._attributes['method'] = method
        self._attributes['action'] = action

    def __build_button(self, kwargs) -> InputButton:
        button_kwargs = {
            'text': kwargs.pop('text', self.text),
            'color': kwargs.pop('color', self.color),
            'css_class': kwargs.pop('button_css_class', self.button_css_class),
            'attributes': kwargs.pop('button_attributes', copy(self.button_attributes)),
            'data_attributes': kwargs.pop('button_data_attributes', copy(self.button_data_attributes))
        }
        if self.close:
            button_kwargs['close'] = True
            button_kwargs['aria_attributes'] = {"label": "Close"}
        button_kwargs['confirm_text'] = kwargs.pop('confirm_text', self.confirm_text)
        return InputButton(**button_kwargs)

    def get_context_data(self, *args, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(*args, **kwargs)
        context['button'] = self.button
        context['data'] = self.data
        return context


class ButtonRow(Block):
    # FIXME: deprecate this in favor of HorizontalLayoutBlock

    def __init__(self, *blocks, **kwargs):
        css_class = kwargs.get("css_class", "")
        css_class += " d-flex justify-content-end"
        kwargs["css_class"] = css_class
        super().__init__(*blocks, **kwargs)
