#!/usr/bin/env python
# -*- coding: utf-8 -*-

from copy import copy
from typing import Dict, Any, Optional

from .base import Block


class Button(Block):
    """
    Render a ``<button>`` with Bootstrap styling.  Example::

        from wildwidgets import Button

        Button(text="My Button")

    When rendered in the template with the ``wildewdigets`` template tag, this will produce::

        <button type="button" class="button btn btn-secondary">My Button</button>

    All the constructor parameters can be set in a subclass of this class as class attributes.  Parameters
    to the constructor override any defined class attributes.

    :param text: The text to use for the button, defaults to 'Button'
    :type text: str
    :param color: The Boostrap color class to use for the button, defaults to 'secondary'
    :type color: str
    :param close: The Boostrap close icon will be used for the button, defaults to False.
    :type close: bool
    :param name: This CSS class will be added to the classes to identify this button, defaults to 'block'
    :type tag: str
    :param modifier: If specified, also add a class named ``{name}--{modifier}`` to the CSS classes, defaults
        to no modifier
    :type modifier: str
    :param css_class: a string of classes to apply to the button, defaults to no classes.
    :type css_class: str
    :param css_id: Use this as the ``id`` attribute for the button, defaults to no ``id``
    :type css_id: str
    :param attributes: Set any additional attributes for the button as key, value pairs, defaults to no additional
        attributes.
    :type attributes: dict(str, str)
    :param data_attributes: Set ``data-`` attributes for the button, defaults to no data attributes
    :type data_attributes: dict(str, str)
    """
    tag: str = 'button'
    block: str = 'button'
    color: str = 'secondary'
    text: str = 'Button'

    def __init__(self, **kwargs):
        color = kwargs.pop('color', self.color)
        text = kwargs.pop('text', self.text)
        close = kwargs.pop('close', False)
        if close:
            text = ""
            kwargs["css_class"]="btn-close"
            kwargs["aria_attributes"]={"label":"Close"}
        super().__init__(text, **kwargs)
        self._content = text
        self._attributes['type'] = 'button'
        if not close:
            if self._css_class:
                self._css_class = f'{self._css_class} btn btn-{color}'
            else:
                self._css_class = f'btn btn-{color}'


class ModalButton(Button):
    """
    Render a ``<button>`` with Bootstrap styling which toggles a Bootstrap modal.  Example::

        from wildwidgets import ModalButton

        ModalButton(text="My Button", target='#mymodal')

    When rendered in the template with the ``wildewdigets`` template tag, this will produce::

        <button type="button" class="button button--modal btn btn-secondary" data-toggle="modal"
          data-target="#mymodal">My Button</button>

    All the constructor parameters can be set in a subclass of this class as class attributes.  Parameters
    to the constructor override any defined class attributes.

    :param text: The text to use for the button, defaults to 'Button'
    :type text: str
    :param color: The Boostrap color class to use for the button, defaults to 'secondary'
    :type color: str
    :param target: The CSS target for the Bootstrap modal, defaults to no target.
    :type target: str
    :param name: This CSS class will be added to the classes to identify this button, defaults to 'block'
    :type tag: str
    :param modifier: If specified, also add a class named ``{name}--{modifier}`` to the CSS classes, defaults
        to no modifier
    :type modifier: str
    :param css_class: a string of classes to apply to the button, defaults to no classes.
    :type css_class: str
    :param css_id: Use this as the ``id`` attribute for the button, defaults to no ``id``
    :type css_id: str
    :param attributes: Set any additional attributes for the button as key, value pairs, defaults to no additional
        attributes.
    :type attributes: dict(str, str)
    :param data_attributes: Set ``data-`` attributes for the button, defaults to no data attributes
    :type data_attributes: dict(str, str)
    """
    block: str = 'button button--modal'
    target: Optional[str] = None

    def __init__(self, **kwargs):
        target = kwargs.pop('target', self.target)
        super().__init__(**kwargs)
        self._data_attributes['toggle'] = 'modal'
        self._data_attributes['target'] = target if target is not None else self.target


class CollapseButton(Button):
    """
    Render a ``<button>`` with Bootstrap styling which toggles a Bootstrap modal.  Example::

        from wildwidgets import ModalButton

        ModalButton(text="My Button", target='#mymodal')

    When rendered in the template with the ``wildewdigets`` template tag, this will produce::

        <button type="button" class="button button--modal btn btn-secondary" data-toggle="modal"
          data-target="#mymodal">My Button</button>

    All the constructor parameters can be set in a subclass of this class as class attributes.  Parameters
    to the constructor override any defined class attributes.

    :param text: The text to use for the button, defaults to 'Button'
    :type text: str
    :param color: The Boostrap color class to use for the button, defaults to 'secondary'
    :type color: str
    :param target: The CSS target for the Bootstrap modal, defaults to no target.
    :type target: str
    :param name: This CSS class will be added to the classes to identify this button, defaults to 'block'
    :type tag: str
    :param modifier: If specified, also add a class named ``{name}--{modifier}`` to the CSS classes, defaults
        to no modifier
    :type modifier: str
    :param css_class: a string of classes to apply to the button, defaults to no classes.
    :type css_class: str
    :param css_id: Use this as the ``id`` attribute for the button, defaults to no ``id``
    :type css_id: str
    :param attributes: Set any additional attributes for the button as key, value pairs, defaults to no additional
        attributes.
    :type attributes: dict(str, str)
    :param data_attributes: Set ``data-`` attributes for the button, defaults to no data attributes
    :type data_attributes: dict(str, str)
    """
    block: str = 'button button--collapse'
    target: Optional[str] = None

    def __init__(self, **kwargs):
        target = kwargs.pop('target', self.target)
        super().__init__(**kwargs)
        self._data_attributes['toggle'] = 'collapse'
        self._data_attributes['target'] = target
        self._aria_attributes['expanded'] = 'false'
        self._aria_attributes['controls'] = target.lstrip("#")


class LinkButton(Button):
    """
    Render an ``<a>`` with Bootstrap button styling which toggles a Bootstrap modal.  Example::

        from wildwidgets import LinkButton

        LinkButton(text="My Button", url='https://myexample.com')

    When rendered in the template with the ``wildewdigets`` template tag, this will produce::

        <a href="https://myexample.com" class="button button--link btn btn-secondary">My Button</a>

    All the constructor parameters can be set in a subclass of this class as class attributes.  Parameters
    to the constructor override any defined class attributes.

    :param text: The text to use for the button, defaults to 'Button'
    :type text: str
    :param color: The Boostrap color class to use for the button, defaults to 'secondary'
    :type color: str
    :param url: The URL for the ``href`` attribute of the <a> record, defaults to no URL.
    :type target: str
    :param name: This CSS class will be added to the classes to identify this button, defaults to 'block'
    :type tag: str
    :param modifier: If specified, also add a class named ``{name}--{modifier}`` to the CSS classes, defaults
        to no modifier
    :type modifier: str
    :param css_class: a string of classes to apply to the button, defaults to no classes.
    :type css_class: str
    :param css_id: Use this as the ``id`` attribute for the button, defaults to no ``id``
    :type css_id: str
    :param attributes: Set any additional attributes for the button as key, value pairs, defaults to no additional
        attributes.
    :type attributes: dict(str, str)
    :param data_attributes: Set ``data-`` attributes for the button, defaults to no data attributes
    :type data_attributes: dict(str, str)
    """
    tag: str = 'a'
    block: str = 'button button--link'
    url: Optional[str] = None

    def __init__(self, **kwargs):
        url = kwargs.pop('url', self.url)
        super().__init__(**kwargs)
        del self._attributes['type']
        if url:
            self._attributes['href'] = url


class InputButton(Button):
    """
    Render an ``<input type="submit">`` with Bootstrap button styling.  Example::

        InputButton(text="Save")

    When rendered in the template with the ``wildewdigets`` template tag, this will produce::

        <input type="submit" class="button button--submit btn btn-secondary" value="Save">

    All the constructor parameters can be set in a subclass of this class as class attributes.  Parameters
    to the constructor override any defined class attributes.

    :param text: The text to use for the button, defaults to 'Button'
    :type text: str
    :param color: The Boostrap color class to use for the button, defaults to 'secondary'
    :type color: str
    :param url: The URL for the ``href`` attribute of the <a> record, defaults to no URL.
    :type target: str
    :param name: This CSS class will be added to the classes to identify this button, defaults to 'block'
    :type tag: str
    :param modifier: If specified, also add a class named ``{name}--{modifier}`` to the CSS classes, defaults
        to no modifier
    :type modifier: str
    :param css_class: a string of classes to apply to the button, defaults to no classes.
    :type css_class: str
    :param css_id: Use this as the ``id`` attribute for the button, defaults to no ``id``
    :type css_id: str
    :param attributes: Set any additional attributes for the button as key, value pairs, defaults to no additional
        attributes.
    :type attributes: dict(str, str)
    :param data_attributes: Set ``data-`` attributes for the button, defaults to no data attributes
    :type data_attributes: dict(str, str)
    """
    template_name: str = 'wildewidgets/block--simple.html'
    tag: str = 'input'
    block: str = 'button--submit'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._attributes['type'] = 'submit'
        self._attributes['value'] = self._content
        self._content = None


class FormButton(Block):
    """
    Render a ``<form>`` with optional hidden inputs and a submit button.

        from wildwidgets import FormButton

        FormButton(text="Save", action='/my/form/action', data={'field1': 'value1'})

    When rendered in the template with the ``wildewdigets`` template tag, this will produce::

        <form action="/my/form/action" method="post" class="button-form">
            <input type="hidden" name="csrfmiddlewaretoken" value="__THE_CSRF_TOKEN__">
            <input type="hidden" name="field1" value="value1">
            <input type="submit" class="button button--submit btn btn-secondary" value="Save">
        </form>

    All the constructor parameters can be set in a subclass of this class as class attributes.  Parameters
    to the constructor override any defined class attributes.

    :param text: The text to use for the button, defaults to 'Button'
    :type text: str
    :param color: The Boostrap color class to use for the button, defaults to 'secondary'
    :type color: str
    :param url: The URL for the ``href`` attribute of the <a> record, defaults to no URL.
    :type target: str
    :param name: This CSS class will be added to the classes to identify this form, defaults to 'button-form'
    :type tag: str
    :param modifier: If specified, also add a class named ``{name}--{modifier}`` to the form CSS classes, defaults
        to no modifier
    :type modifier: str
    :param css_class: a string of classes to apply to the form, defaults to no classes.
    :type css_class: str
    :param button_css_class: a string of classes to apply to the button, defaults to no classes.
    :type button_css_class: str
    :param css_id: Use this as the ``id`` attribute for the form, defaults to no ``id``
    :type css_id: str
    :param attributes: Set any additional attributes for the form as key, value pairs, defaults to no additional
        attributes.
    :type attributes: dict(str, str)
    :param button_attributes: Set any additional attributes for the button as key, value pairs, defaults to no
        additional attributes.
    :type attributes: dict(str, str)
    :param data_attributes: Set ``data-`` attributes for the form, defaults to no data attributes
    :type data_attributes: dict(str, str)
    :param button_data_attributes: Set ``data-`` attributes for the button, defaults to no data attributes
    :type button_data_attributes: dict(str, str)
    """
    template_name = 'wildewidgets/button--form.html'
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
            button_kwargs['aria_attributes'] = {"label":"Close"}
        confirm_text = kwargs.pop('confirm_text', self.confirm_text)
        if confirm_text is not None:
            button_kwargs['attributes']['onclick'] = f"return confirm('{confirm_text}');"
        return InputButton(**button_kwargs)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['button'] = self.button
        context['data'] = self.data
        return context


class ButtonRow(Block):

    def __init__(self, *blocks, **kwargs):
        css_class = kwargs.get("css_class", "")
        css_class += " d-flex justify-content-end"
        kwargs["css_class"] = css_class
        super().__init__(*blocks, **kwargs)
