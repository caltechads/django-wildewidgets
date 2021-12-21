#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random

from django import template

from wildewidgets.views import JSONDataView

from ..base import Widget


class AltairChart(Widget, JSONDataView):
    template_file = 'wildewidgets/altairchart.html'
    title = None
    width = "100%"
    height = "300px"

    def __init__(self, *args, **kwargs):
        self.data = None
        self.options = {
            'width': kwargs.get('width', self.width),
            'height': kwargs.get('height', self.height),
            "title": kwargs.get('title', self.title)
        }

    def get_content(self, **kwargs):
        chart_id = random.randrange(0, 1000)
        template_file = self.template_file
        if self.data:
            context = self.get_context_data()
        else:
            context = {"async": True}
        html_template = template.loader.get_template(template_file)
        context['options'] = self.options
        context['name'] = f"altair_chart_{chart_id}"
        context["wildewidgetclass"] = self.__class__.__name__
        content = html_template.render(context)
        return content

    def __str__(self):
        return self.get_content()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.load()
        context.update({"data": self.data})
        return context

    def set_data(self, spec, set_size=True):
        if set_size:
            self.data = spec.properties(
                width="container",
                height="container"
            ).to_dict()
        else:
            self.data = spec.to_dict()

    def load(self):
        pass
