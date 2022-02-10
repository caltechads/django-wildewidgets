#!/usr/bin/env python
# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from wildewidgets.widgets.text import StringBlock

from .base import Block
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
