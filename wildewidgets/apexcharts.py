import json
import random

from .wildewidgets import WidgetInitKwargsMixin
from .ui import TemplateWidget


class ApexDatasetBase():
    name = ""
    type = None
    
    def __init__(self, **kwargs):
        self.data = []

    def get_options(self):
        options = {
            'data': self.data
        }
        if self.name:
            options['name'] = self.name
        if self.type:
            options['type'] = self.type
        return options


class ApexChartBase(WidgetInitKwargsMixin, TemplateWidget):
    template_name = 'wildewidgets/apex_chart.html'
    css_id = None
    chart_type = None

    def __init__(self, *args, **kwargs):
        self.options = {}
        self.options['series'] = []
        self.css_id = kwargs.get('css_id', self.css_id)
        self.options['chart'] = {}
        if self.chart_type:
            self.options['chart']['type'] = self.chart_type

    def add_dataset(self, dataset):
        self.options['series'].append(dataset.get_options())

    def add_categories(self, categories):
        if not 'xaxis' in self.options:
            self.options['xaxis'] = {}
        self.options['xaxis']['categories'] = categories

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['options'] = json.dumps(self.options)
        if not self.css_id:
            self.css_id = random.randint(1, 100000)
        kwargs['css_id'] = self.css_id
        return kwargs

    def add_suboption(self, option, name, value):
        if option not in self.options:
            self.options[option] = {}
        self.options[option][name] = value


class ApexSparkline(ApexChartBase):
    width = 65
    stroke_width = 2
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_suboption('chart', 'sparkline', {'enabled': True})
        self.add_suboption('chart', 'width', self.width)
        self.add_suboption('stroke', 'width', self.stroke_width)


