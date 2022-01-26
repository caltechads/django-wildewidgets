#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
from urllib.parse import urlencode

from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import InvalidPage, Paginator
from django.db.models import QuerySet
from django.http import Http404

from .base import TemplateWidget, Block

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
    title = None
    subtitle = None
    widget = None
    widget_css = None
    css_class = None

    def __init__(self, **kwargs):
        self.header = kwargs.get('header', self.header)
        self.header_text = kwargs.get('header_text', self.header_text)
        self.title = kwargs.get('title', self.title)
        self.subtitle = kwargs.get('subtitle', self.subtitle)
        self.widget = kwargs.get('widget', self.widget)
        self.widget_css = kwargs.get('widget_css', self.widget_css)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['header'] = self.header
        kwargs['header_text'] = self.header_text
        kwargs['title'] = self.title
        kwargs['subtitle'] = self.subtitle
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


class PagedModelWidget(Block):
    template_name = 'wildewidgets/paged_model_widget.html'
    model = None
    model_widget = None
    ordering = None
    page_kwarg = 'page'
    paginate_by = None
    queryset = None
    max_page_controls = 5
    css_class = "wildewidgets-paged-model-widget bg-white shadow-sm"

    def __init__(self, *args, **kwargs): #model=None, model_widget=None, ordering=None, page_kwarg=None, paginate_by=None, queryset=None, extra_url={}, **kwargs):
        self.model = kwargs.pop('model', self.model)
        self.model_widget = kwargs.pop('model_widget', self.model_widget)
        self.ordering = kwargs.pop('ordering', self.ordering)
        self.page_kwarg = kwargs.pop('page_kwarg', self.page_kwarg)
        self.paginate_by = kwargs.pop('paginate_by', self.paginate_by)
        self.queryset = kwargs.pop('queryset', self.queryset)
        self.extra_url = kwargs.pop('extra_url', {})
        super().__init__(*args, **kwargs)

    def get_model_widgets(self, object_list):
        widgets = []
        for object in object_list:
            widgets.append(self.model_widget(object=object))
        return widgets


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
        if self.extra_url:
            anchor = self.extra_url.pop("#", None)
            extra_url = f"&{urlencode(self.extra_url)}"
            if anchor:
                extra_url = f"{extra_url}#{anchor}"
            kwargs['extra_url'] = extra_url
        else:
            kwargs['extra_url'] = ''
        return kwargs

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


class CrispyFormWidget(Block):
    template_name = 'wildewidgets/crispy_form_widget.html'
    css_class = "wildewidgets-crispy-form-widget"

    def __init__(self, *args, form=None, **kwargs): 
        super().__init__(*args, **kwargs)    
        self.form = form

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['form'] = self.form
        return kwargs


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
