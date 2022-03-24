#!/usr/bin/env python
# -*- coding: utf-8 -*-
from copy import copy
import random
from urllib.parse import urlencode

from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import InvalidPage, Paginator
from django.db.models import QuerySet
from django.http import Http404

from .base import TemplateWidget, Block
from .text import HTMLWidget, StringBlock
from .buttons import FormButton
from .headers import CardHeader

from django.core.exceptions import ImproperlyConfigured


class TabbedWidget(TemplateWidget):
    template_name = 'wildewidgets/tabbed_widget.html'
    slug_suffix = None

    def __init__(self, *args, **kwargs):
        self.tabs = []

    def add_tab(self, name, widget):
        self.tabs.append((name, widget))

    def get_context_data(self, **kwargs):
        kwargs['tabs'] = self.tabs
        if not self.slug_suffix:
            self.slug_suffix = random.randrange(0, 10000)
        kwargs['identifier'] = self.slug_suffix
        return kwargs


class CardWidget(TemplateWidget):
    template_name = 'wildewidgets/card.html'
    header = None
    header_text = None
    card_title = None
    card_subtitle = None
    widget = None
    widget_css = None
    css_class = None

    def __init__(self, **kwargs):
        self.header = kwargs.get('header', self.header)
        self.header_text = kwargs.get('header_text', self.header_text)
        if self.header_text and not self.header:
            self.header = CardHeader(header_text=self.header_text)
        self.card_title = kwargs.get('card_title', self.card_title)
        self.card_subtitle = kwargs.get('card_subtitle', self.card_subtitle)
        self.widget = kwargs.get('widget', self.widget)
        self.widget_css = kwargs.get('widget_css', self.widget_css)
        self.css_class = kwargs.get("css_class", self.css_class)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['header'] = self.header
        kwargs['header_text'] = self.header_text
        kwargs['title'] = self.card_title
        kwargs['subtitle'] = self.card_subtitle
        kwargs['widget'] = self.widget
        kwargs['widget_css'] = self.widget_css
        kwargs['css_class'] = self.css_class

        if not self.widget:
            raise ImproperlyConfigured("You must define a widget.")
        return kwargs

    def set_widget(self, widget, css_class=None):
        self.widget = widget
        self.widget_css = css_class

    def set_header(self, header):
        self.header = header


class MultipleModelWidget(Block):
    model = None
    model_widget = None
    model_kwargs = {}
    ordering = None
    queryset = None
    item_label="item"

    def __init__(self, *args, item_label="", **kwargs):
        self.model = kwargs.pop('model', self.model)
        self.model_widget = kwargs.pop('model_widget', self.model_widget)
        self.ordering = kwargs.pop('ordering', self.ordering)
        self.queryset = kwargs.pop('queryset', self.queryset)
        self.model_kwargs = kwargs.pop('model_kwargs', copy(self.model_kwargs))
        self.item_label = item_label if item_label else self.item_label
        super().__init__(*args, **kwargs)

    def get_item_label(self, object):
        return self.item_label

    def get_model_widget(self, object=object, **kwargs):
        if self.model_widget:
            return self.model_widget(object=object, **kwargs)
        else:
            raise ImproperlyConfigured(
                "%(cls)s is missing a model widget. Define "
                "%(cls)s.model_widget or override "
                "%(cls)s.get_model_widget()." % {'cls': self.__class__.__name__}
            )

    def get_model_widgets(self, object_list):
        widgets = []
        for object in object_list:
            widgets.append(self.get_model_widget(object=object, **self.model_kwargs))
        return widgets

    def get_queryset(self):
        """
        Return the list of items for this widget.
        The return value must be an iterable and may be an instance of
        `QuerySet` in which case `QuerySet` specific behavior will be enabled.
        """
        if self.queryset is not None:
            queryset = self.queryset
            if isinstance(queryset, QuerySet):
                queryset = queryset.all()
        elif self.model is not None:
            queryset = self.model._default_manager.all()
        else:
            raise ImproperlyConfigured(
                "%(cls)s is missing a QuerySet. Define "
                "%(cls)s.model, %(cls)s.queryset, or override "
                "%(cls)s.get_queryset()." % {
                    'cls': self.__class__.__name__
                }
            )
        ordering = self.ordering
        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)
            queryset = queryset.order_by(*ordering)
        return queryset


class PagedModelWidget(MultipleModelWidget):
    template_name = 'wildewidgets/paged_model_widget.html'
    page_kwarg = 'page'
    paginate_by = None
    max_page_controls = 5
    css_class = "wildewidgets-paged-model-widget "

    def __init__(self, *args, **kwargs):
        self.page_kwarg = kwargs.pop('page_kwarg', self.page_kwarg)
        self.paginate_by = kwargs.pop('paginate_by', self.paginate_by)
        self.extra_url = kwargs.pop('extra_url', {})
        super().__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        self.request = kwargs.get('request')
        if self.paginate_by:
            paginator = Paginator(self.get_queryset(), self.paginate_by)
            page_number = self.request.GET.get(self.page_kwarg)
            try:
                page_number = int(page_number)
            except (TypeError, ValueError):
                page_number = 1
            try:
                page = paginator.page(page_number)
                kwargs['widget_list'] = self.get_model_widgets(page.object_list)
                kwargs['page_obj'] = page
                kwargs['is_paginated'] = page.has_other_pages()
                kwargs['paginator'] = paginator
                kwargs['page_kwarg'] = self.page_kwarg
                pages = kwargs['page_obj'].paginator.num_pages
                if pages > self.max_page_controls:
                    pages = self.max_page_controls
                page_number = page.number
                max_controls_half = int(self.max_page_controls / 2)
                range_start = 1 if page_number - max_controls_half < 1 else page_number - max_controls_half
                kwargs['page_range'] = range(range_start, range_start+pages)
            except InvalidPage as e:
                raise Http404(
                    'Invalid page (%(page_number)s): %(message)s' % {
                        'page_number': page_number,
                        'message': str(e)
                    }
                )
        else:
            kwargs['widget_list'] = self.get_model_widgets(self.get_queryset().all())
        kwargs['item_label'] = self.item_label
        if self.extra_url:
            anchor = self.extra_url.pop("#", None)
            extra_url = f"&{urlencode(self.extra_url)}"
            if anchor:
                extra_url = f"{extra_url}#{anchor}"
            kwargs['extra_url'] = extra_url
        else:
            kwargs['extra_url'] = ''
        return kwargs


class CrispyFormWidget(Block):
    template_name = 'wildewidgets/crispy_form_widget.html'
    css_class = "wildewidgets-crispy-form-widget"

    def __init__(self, *args, form=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.form = form

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        if self.form:
            kwargs['form'] = self.form
        return kwargs


class CollapseWidget(Block):
    css_class="collapse"

    def __init__(self, *args, **kwargs):
        if "css_class" in kwargs:
            kwargs['css_class'] = f"{kwargs['css_class']} collapse"
        else:
            kwargs['css_class'] = self.css_class
        super().__init__(*args, **kwargs)


class HorizontalLayoutBlock(Block):
    align="center"
    justify="between"

    def __init__(self, *blocks, **kwargs):
        align = kwargs.pop("align", self.align)
        justify = kwargs.pop("justify", self.justify)
        css_class = kwargs.get("css_class", "")
        css_class += f" d-flex align-items-{align} justify-content-{justify}"
        kwargs["css_class"] = css_class
        super().__init__(*blocks, **kwargs)


class ListModelWidget(MultipleModelWidget):
    """
    Extend `MultipleModelWidget`. This class provides a list of objects
    defined by a QuerySet, displayed in a list-group `ul` block. By default,
    a widget will be provided that simply displays whatever returns from
    the conversion of the object to a `str`. If a `remove_url` is provided,
    an `X` icon to the right of each object will act as a button to remove
    the item.

    Example 1:

        widget = ListModelWidget(
            queryset=myparent.children,
            item_label='child',
            remove_url=reverse('remove_url') + "?id={}",
        )
    """
    base_css_class = "wildewidgets-list-model-widget list-group"
    tag='ul'
    remove_url=None

    def __init__(self, *args, remove_url=None, **kwargs):
        self.remove_url = remove_url if remove_url else self.remove_url
        css_class = kwargs.get("css_class", "")
        css_class += f" {self.base_css_class}"
        kwargs["css_class"] = css_class.strip()
        super().__init__(*args, **kwargs)
        self.remove_url = remove_url
        super().__init__(*args, **kwargs)
        widgets = self.get_model_widgets(self.get_queryset().all())
        if not widgets:
            self.add_block(StringBlock(f"No {self.item_label}s", tag='li', css_class="list-group-item fw-light fst-italic"))
        for widget in widgets:
            self.add_block(widget)

    def get_remove_url(self, object):
        if self.remove_url:
            return self.remove_url.format(object.id)
        return ""

    def get_confirm_text(self, object):
        item_label = self.get_item_label(object)
        return f"Are you sure you want to remove this {item_label}?"

    def get_object_text(self, object):
        return str(object)

    def get_model_widget(self, object=object, **kwargs):
        if self.model_widget:
            return super().get_model_widget(object=object, **kwargs)
        widget = HorizontalLayoutBlock(
            tag='li',
            css_class='list-group-item'
        )
        if hasattr(object, 'get_absolute_url'):
            url = object.get_absolute_url()
            widget.add_block(HTMLWidget(html=f'<a href="{url}">{str(object)}</a>'))
        else:
            widget.add_block(StringBlock(self.get_object_text(object)))
        remove_url = self.get_remove_url(object)
        if remove_url:
            widget.add_block(
                FormButton(
                    close=True,
                    action=remove_url,
                    confirm_text=self.get_confirm_text(object),
                ),
            )
        return widget

