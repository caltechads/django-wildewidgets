#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Dict, Any, Optional, Union

from .base import Block, TemplateWidget, Image
from .structure import HorizontalLayoutBlock
from .text import CodeWidget


class KeyValueListBlock(Block):

    tag: str = 'ul'
    block: str = "list-group"

    def add_simple_key_value(self, key, value):
        self.add_block(
            HorizontalLayoutBlock(
                Block(key),
                Block(value),
                tag="li",
                css_class="list-group-item",
            )
        )

    def add_code_key_value(self, key, value, language=None):
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

    block: str = 'rounded-circle'

    #: The gravatar URL
    gravatar_url: Optional[str] = None
    #: The length in pixels that will used as the height and width of the image
    size: Union[int, str] = 28
    #: The person's name.  This will be used as the ``alt`` tag on the image
    fullname: Optional[str] = None

    def __init__(
        self,
        gravatar_url: str = None,
        size: Union[int, str] = None,
        fullname: str = None,
        **kwargs
    ):
        self.gravatar_url = gravatar_url if gravatar_url is not None else self.gravatar_url
        self.size = size if size is not None else self.size
        self.fullname = fullname if fullname is not None else self.fullname
        try:
            int(self.size)
        except ValueError as e:
            raise ValueError(f'size should be an integer; got "{self.size}" instead') from e
        kwargs['src'] = self.gravatar_url
        if self.fullname:
            kwargs['alt'] = self.fullname
        super().__init__(**kwargs)
        self._attributes['style'] = f'width: {self.size}px; height: {self.size}px'


class InitialsAvatarWidget(TemplateWidget):

    template_name: str = 'wildewidgets/initials_avatar.html'

    #: The length in pixels that will used as the height and width of the gravatar
    size: int = 28
    #: The foreground color for the gravatar
    color: str = "white"
    #: The background color for the gravatar
    background_color: str = "#626976"

    def __init__(
        self,
        *args,
        initials: str = None,
        size: int = None,
        color: str = None,
        background_color: str = None,
        fullname: str = None,
        **kwargs
    ):
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
