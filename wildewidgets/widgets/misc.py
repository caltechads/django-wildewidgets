#!/usr/bin/env python
# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from wildewidgets.widgets.text import StringBlock

from .base import Block, TemplateWidget
from .structure import HorizontalLayoutBlock
from .text import (
    CodeWidget,
    StringBlock,
)

@dataclass
class BreadcrumbItem:
    title: str
    url: str


class BreadrumbBlock(Block):
    template_name: str = 'wildewidgets/breadcrumb_block.html'
    tag: str = 'nav'
    aria_attributes: Dict[str, str] = {'label':'breadcrumb'}
    title_class: str = ""

    def __init__(self, *args, **kwargs):
        self.title_class = kwargs.pop('title_class', self.title_class)
        super().__init__(*args, **kwargs)
        self.items = []

    def add_breadcrumb(self, title, url=None):
        self.items.append(BreadcrumbItem(title, url))

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        kwargs = super().get_context_data(**kwargs)
        kwargs['items'] = self.items
        kwargs['title_class'] = self.title_class        
        return kwargs

    def flatten(self):
        return ' - '.join([item.title for item in self.items])


class KeyValueListBlock(Block):
    tag = 'ul'
    css_class = "list-group"

    def __init__(self, *args, **kwargs):
        if "css_class" in kwargs:
            kwargs['css_class'] = f"{kwargs['css_class']} {self.css_class}"
        else:
            kwargs['css_class'] = self.css_class
        super().__init__(*args, **kwargs)

    def add_simple_key_value(self, key, value):
        self.add_block(
            HorizontalLayoutBlock(
                StringBlock(key),
                StringBlock(value),
                tag = "li",
                css_class = "list-group-item",
            )
        )

    def add_code_key_value(self, key, value, language=None):
        self.add_block(
            Block(
                StringBlock(key),
                CodeWidget(
                    code=value, 
                    language=language,
                    css_class="m-3",
                ),
                tag = "li",
                css_class = "list-group-item",
            )
        )


class GravatarWidget(TemplateWidget):
    template_name = 'wildewidgets/gravatar.html'
    css_class = "rounded-circle"
    size = "28"

    def __init__(self, *args, gravatar_url=None, size=None, fullname=None, **kwargs):
        self.gravatar_url = gravatar_url
        self.css_class = kwargs.pop('css_class', self.css_class)
        self.size = size or self.size
        self.fullname = fullname
        super().__init__(*args, **kwargs)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        kwargs = super().get_context_data(**kwargs)
        kwargs['gravatar_url'] = self.gravatar_url
        kwargs['css_class'] = self.css_class
        kwargs['size'] = self.size
        kwargs['fullname'] = self.fullname
        return kwargs


class InitialsAvatarWidget(TemplateWidget):
    template_name = 'wildewidgets/initials_avatar.html'
    size = 28
    color = "white"
    background_color = "#626976"

    def __init__(self, *args, initials=None, size=None, color=None, background_color=None, fullname=None, **kwargs):
        self.initials = initials
        self.size = size or self.size
        self.color = color or self.color
        self.background_color = background_color or self.background_color
        self.fullname = fullname
        super().__init__(*args, **kwargs)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        kwargs = super().get_context_data(**kwargs)
        kwargs['initials'] = self.initials.upper()
        kwargs['fullsize'] = str(self.size)
        kwargs['halfsize'] = str(self.size/2)
        kwargs['color'] = self.color
        kwargs['background_color'] = self.background_color
        kwargs['fullname'] = self.fullname
        return kwargs
