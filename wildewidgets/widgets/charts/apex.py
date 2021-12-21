#!/usr/bin/env python
# -*- coding: utf-8 -*-


import json
import random
from typing import Optional

from django import template
from django.http import JsonResponse

from wildewidgets.views import WidgetInitKwargsMixin

from ..base import Widget


class ApexDatasetBase(Widget):
    name: Optional[str] = None
    chart_type: Optional[str] = None

    def __init__(self, **kwargs):
        self.data = []

    def get_options(self):
        options = {
            'data': self.data
        }
        if self.name:
            options['name'] = self.name if self.name is not None else ""
        if self.type:
            options['type'] = self.chart_type
        return options


class ApexJSONMixin:
    """
    A mixin class adding AJAX support to Apex Charts
    """
    template_name: str = 'wildewidgets/apex_json.html'

    def dispatch(self, request, *args, **kwargs):
        handler = getattr(self, request.method.lower())
        return handler(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        data = self.get_series_data()
        return self.render_to_response(data)

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context)

    def get_series_data(self, **kwargs):
        self.load()
        kwargs['series'] = self.chart_options['series']
        return kwargs

    def load(self):
        """
        Load datasets into the chart via AJAX.
        """
        pass


class ApexChartBase(WidgetInitKwargsMixin):
    template_name = 'wildewidgets/apex_chart.html'
    css_id = None
    chart_type = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chart_options = {}
        self.chart_options['series'] = []
        self.css_id = kwargs.get('css_id', self.css_id)
        self.chart_options['chart'] = {}
        if self.chart_type:
            self.chart_options['chart']['type'] = self.chart_type

    def add_dataset(self, dataset):
        self.chart_options['series'].append(dataset.get_options())

    def add_categories(self, categories):
        if 'xaxis' not in self.chart_options:
            self.chart_options['xaxis'] = {}
        self.chart_options['xaxis']['categories'] = categories

    def get_context_data(self, **kwargs):
        # kwargs = super().get_context_data(**kwargs)
        kwargs['options'] = json.dumps(self.chart_options)
        if not self.css_id:
            self.css_id = random.randint(1, 100000)
        kwargs['css_id'] = self.css_id
        kwargs["wildewidgetclass"] = self.__class__.__name__
        kwargs["extra_data"] = self.get_encoded_extra_data()
        return kwargs

    def add_suboption(self, option, name, value):
        if option not in self.chart_options:
            self.chart_options[option] = {}
        self.chart_options[option][name] = value

    def __str__(self):
        return self.get_content()

    def get_content(self, **kwargs):
        context = self.get_context_data()
        html_template = template.loader.get_template(self.template_name)
        content = html_template.render(context)
        return content


class ApexSparkline(ApexChartBase):
    width = 65
    stroke_width = 2

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_suboption('chart', 'sparkline', {'enabled': True})
        self.add_suboption('chart', 'width', self.width)
        self.add_suboption('stroke', 'width', self.stroke_width)
