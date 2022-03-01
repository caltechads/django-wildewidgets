#!/usr/bin/env python
# -*- coding: utf-8 -*-

from copy import copy
from typing import Union, List, Dict, Any, Optional

from django.template.loader import get_template


class Widget:
    """
    The base class form which all widgets should inherit.
    """
    title: Optional[Union[str, "Widget"]] = None
    icon: str = 'gear'

    def __init__(self, title: Union[str, "Widget"] = None, icon=None, **kwargs):
        self.title = title if title else self.title
        self.icon = icon if icon else self.icon
        super().__init__(**kwargs)

    def get_title(self) -> Union[str, "Widget"]:
        return self.title

    def is_visible(self) -> bool:
        return True

    def get_content(self) -> "Widget":
        raise NotImplementedError


class TemplateWidget(Widget):
    template_name: str

    def get_content(self, **kwargs) -> str:
        context = self.get_context_data(**kwargs)
        html_template = get_template(self.template_name)
        content = html_template.render(context)
        return content

    def __str__(self) -> str:
        return self.get_content()

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        return kwargs


class Block(TemplateWidget):
    """
    Render a single HTML element.   Example::

        Block('Hello World', tag='a', name='foo', modifier='bar', css_class='blah dah',
            attributes={'href': 'https://example.com'})

    When rendered in the template with the ``wildewdigets`` template tag, this will produce::

        <a href="https://example.com" class="foo foo--bar blah dah">Hello World</a>

    All the constructor parameters can be set in a subclass of this class as class attributes.  Parameters
    to the constructor override any defined class attributes.

    :param *blocks: any content to be rendered in the block, including other blocks.
    :type *blocks: list of strings or other blocks
    :param tag: the name of the element to use, defaults to 'div'
    :type tag: str
    :param name: This CSS class will be added to the classes to identify this element, defaults to 'block'
    :type tag: str
    :param modifier: If specified, also add a class named ``{name}--{modifier}`` to the CSS classes, defaults
        to no modifier
    :type modifier: str
    :param css_class: a string of classes to apply to the element, defaults to no classes.
    :type css_class: str
    :param css_id: Use this as the ``id`` attribute for the element, defaults to no ``id``
    :type css_id: str
    :param content: Set this as the content for the element, defaults to no content.
    :type content: str or :class:`wildewidgets.Widget`
    :param attributes: Set any additional attributes for the element as key, value pairs, defaults to no additional
        attributes.
    :type attributes: dict(str, str)
    :param data_attributes: Set ``data-`` attributes for the element, defaults to no data attributes
    :type modifier: dict(str, str)
    """
    template_name: str = "wildewidgets/block.html"

    # block is the official wildewidgets name of the block; it can't be changed by constructor
    # kwargs
    block: str = 'block'

    tag: str = 'div'
    name: Optional[str] = None
    modifier: Optional[str] = None
    css_class: Optional[str] = None
    css_id: Optional[str] = None
    content: Optional[Union[str, Widget]] = None
    attributes: Dict[str, str] = {}
    data_attributes: Dict[str, str] = {}
    aria_attributes: Dict[str, str] = {}

    def __init__(self, *blocks, tag=None, name=None, modifier=None, css_class=None, css_id=None,
                 attributes=None, data_attributes=None, aria_attributes=None):
        self._name = name if name is not None else copy(self.name)
        self._modifier = modifier if modifier is not None else self.modifier
        self._css_class = css_class if css_class is not None else self.css_class
        self._css_id = css_id if css_id is not None else self.css_id
        self._tag = tag if tag is not None else self.tag
        self._attributes = attributes if attributes is not None else copy(self.attributes)
        self._data_attributes = data_attributes if data_attributes is not None else copy(self.data_attributes)
        self._aria_attributes = aria_attributes if aria_attributes is not None else copy(self.aria_attributes)
        self.blocks = []
        for block in blocks:
            self.add_block(block)

    def add_block(self, block):
        self.blocks.append(block)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        css_class = self._css_class if self._css_class is not None else ''
        name = self._name if self._name is not None else ''
        block = self.block if self.block is not None else ''
        if name and self._modifier:
            modifier = f'{name}--{self.modifier}'
        else:
            modifier = ''
        context['tag'] = self._tag
        context['block_name'] = block
        context['name'] = name
        context['css_classes'] = ' '.join([name, modifier, block, css_class]).strip()
        context['css_id'] = self._css_id
        context['blocks'] = self.blocks
        context['attributes'] = self._attributes
        context['data_attributes'] = self._data_attributes
        context['aria_attributes'] = self._aria_attributes
        return context


class WidgetStream(Block):
    template_name: str = 'wildewidgets/widget_stream.html'
    block: str = 'widget-stream'
    widgets: List[Widget] = []

    def __init__(self, **kwargs):
        self._widgets: List[Widget] = copy(kwargs.pop('widgets', self.widgets))
        super().__init__(**kwargs)

    @property
    def is_empty(self) -> bool:
        return len(self._widgets) == 0

    def add_widget(self, widget, **kwargs):
        wrapper = Block(widget, **kwargs)
        wrapper.block = f"{self.block}__widget"
        self._widgets.append(wrapper)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['widgets'] = self._widgets
        return context
