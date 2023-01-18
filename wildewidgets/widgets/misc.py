#!/usr/bin/env python
# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Dict, Any

from .base import Block, TemplateWidget
from .structure import HorizontalLayoutBlock
from .text import (
    CodeWidget,
    StringBlock,
)


class KeyValueListBlock(Block):

    tag: str = 'ul'
    block: str = "list-group"

    def add_simple_key_value(self, key, value):
        self.add_block(
            HorizontalLayoutBlock(
                StringBlock(key),
                StringBlock(value),
                tag="li",
                css_class="list-group-item",
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
                tag="li",
                css_class="list-group-item",
            )
        )


class GravatarWidget(TemplateWidget):

    template_name: str = 'wildewidgets/gravatar.html'
    css_class: str = "rounded-circle"
    size: str = "28"

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

    template_name: str = 'wildewidgets/initials_avatar.html'
    size: int = 28
    color: str = "white"
    background_color: str = "#626976"

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
        kwargs['halfsize'] = str(self.size / 2)
        kwargs['color'] = self.color
        kwargs['background_color'] = self.background_color
        kwargs['fullname'] = self.fullname
        return kwargs
