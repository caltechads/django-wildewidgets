#!/usr/bin/env python
# -*- coding: utf-8 -*-
import math
import random

from django import template
from django.conf import settings

from wildewidgets.views import WidgetInitKwargsMixin, JSONDataView

from ..base import Widget


class CategoryChart(Widget, WidgetInitKwargsMixin, JSONDataView):

    COLORS = [
        (0, 59, 76),
        (0, 88, 80),
        (100, 75, 120),
        (123, 48, 62),
        (133, 152, 148),
        (157, 174, 136),
        (159, 146, 94),
        (242, 211, 131),
        (30, 152, 138),
        (115, 169, 80)
    ]

    GRAYS = [
        (200, 200, 200),
        (229, 229, 229),
        (170, 169, 159),
        (118, 119, 123),
        (97, 98, 101),
        (175, 175, 175),
        (105, 107, 115),
    ]
    template_file = 'wildewidgets/categorychart.html'
    legend = False
    legend_position = "top"
    color = True

    def __init__(self, *args, **kwargs):
        self.options = {
            'width':  kwargs.get('width', '400px'),
            'height':  kwargs.get('height', '400px'),
            "title": kwargs.get('title', None),
            "legend": kwargs.get('legend', self.legend),
            "legend_position": kwargs.get('legend_position', self.legend_position),
            "chart_type": kwargs.get('chart_type', None),
            "histogram": kwargs.get('histogram', False),
            "max": kwargs.get('max', None),
            "thousands": kwargs.get('thousands', False),
            "histogram_max": kwargs.get('histogram_max', None),
            "url": kwargs.get('url', None)
        }
        self.chart_id = kwargs.get('chart_id', None)
        self.categories = None
        self.datasets = []
        self.dataset_labels = []
        self.color = kwargs.get('color', self.color)
        self.colors = []
        if hasattr(settings, 'CHARTJS_FONT_FAMILY'):
            self.options['chartjs_font_family'] = settings.CHARTJS_FONT_FAMILY
        if hasattr(settings, 'CHARTJS_TITLE_FONT_SIZE'):
            self.options['chartjs_title_font_size'] = settings.CHARTJS_TITLE_FONT_SIZE
        if hasattr(settings, 'CHARTJS_TITLE_FONT_STYLE'):
            self.options['chartjs_title_font_style'] = settings.CHARTJS_TITLE_FONT_STYLE
        if hasattr(settings, 'CHARTJS_TITLE_PADDING'):
            self.options['chartjs_title_padding'] = settings.CHARTJS_TITLE_PADDING
        super().__init__(*args, **kwargs)

    def set_categories(self, categories):
        self.categories = categories

    def add_dataset(self, dataset, label=None):
        self.datasets.append(dataset)
        self.dataset_labels.append(label)

    def set_option(self, name, value):
        self.options[name] = value

    def set_color(self, color):
        self.color = color

    def set_colors(self, colors):
        self.colors = colors

    def get_content(self, **kwargs):
        if self.chart_id:
            chart_id = self.chart_id
        else:
            chart_id = random.randrange(0, 1000)
        template_file = self.template_file
        if self.datasets:
            context = self.get_context_data()
        else:
            context = {"async": True}
        html_template = template.loader.get_template(template_file)
        context['options'] = self.options
        context['name'] = f"chart_{chart_id}"
        context["wildewidgetclass"] = self.__class__.__name__
        context["extra_data"] = self.get_encoded_extra_data()
        content = html_template.render(context)
        return content

    def __str__(self):
        return self.get_content()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.load()
        context.update({"labels": self.get_categories(), "datasets": self.get_dataset_configs()})
        return context

    def get_color_iterator(self):
        if self.colors:
            return iter(self.colors)
        elif self.color:
            return iter(self.COLORS)
        else:
            return iter(self.GRAYS)

    def get_dataset_options(self, index, color):
        default_opt = {
            "backgroundColor": "rgba(%d, %d, %d, 0.5)" % color,
            "borderColor": "rgba(%d, %d, %d, 1)" % color,
            "borderWidth": 0.2,
            # "pointBackgroundColor": "rgba(%d, %d, %d, 1)" % color,
            # "pointBorderColor": "#fff",
        }
        return default_opt

    def get_dataset_configs(self):
        return []

    def get_categories(self):
        if self.categories:
            return self.categories
        raise NotImplementedError(  # pragma: no cover
            "You should return a labels list. " '(i.e: ["January", ...])'
        )

    def get_datasets(self):
        if self.datasets:
            return self.datasets
        raise NotImplementedError(  # pragma: no cover
            "You should return a data list list. " "(i.e: [[25, 34, 0, 1, 50], ...])."
        )

    def get_dataset_labels(self):
        return self.dataset_labels

    def load(self):
        pass


class DoughnutChart(CategoryChart):

    def __init__(self, *args, **kwargs):
        if 'chart_type' not in kwargs:
            kwargs['chart_type'] = "doughnut"
        super().__init__(*args, **kwargs)

    def get_dataset_configs(self):
        datasets = []
        color_generator = self.get_color_iterator()
        data = self.get_dataset()
        dataset = {"data": data}
        dataset["backgroundColor"] = []
        for j in range(len(data)):
            color = tuple(next(color_generator))
            dataset['backgroundColor'].append("rgba(%d, %d, %d)" % color)
        datasets.append(dataset)
        return datasets

    def get_dataset(self):
        return self.datasets[0]


class PieChart(DoughnutChart):

    def __init__(self, *args, **kwargs):
        kwargs['chart_type'] = "pie"
        super().__init__(*args, **kwargs)


class BarChart(CategoryChart):

    def __init__(self, *args, **kwargs):
        if "chart_type" not in kwargs:
            kwargs["chart_type"] = "bar"
        super().__init__(*args, **kwargs)
        self.set_option("money", kwargs.get('money', False))
        self.set_option("stacked", kwargs.get('stacked', False))
        self.set_option("xAxes_name", kwargs.get('xAxes_name', "xAxes"))
        self.set_option("yAxes_name", kwargs.get('yAxes_name', 'yAxes'))

    def set_stacked(self, stacked):
        self.set_option('stacked', "true" if stacked else "false")

    def set_horizontal(self, horizontal):
        if horizontal:
            self.options["xAxes_name"] = "yAxes"
            self.options["yAxes_name"] = "xAxes"
            self.options["chart_type"] = "horizontalBar"
        else:
            self.options["xAxes_name"] = "xAxes"
            self.options["yAxes_name"] = "yAxes"
            self.options["chart_type"] = "bar"

    def get_dataset_options(self, index, color):
        default_opt = {
            "backgroundColor": "rgba(%d, %d, %d, 0.65)" % color
            # "borderColor": "rgba(%d, %d, %d, 1)" % color,
            # "borderWidth": 0.2,
        }
        if not self.options['histogram']:
            default_opt['borderColor'] = "rgba(%d, %d, %d, 1)" % color
            default_opt['borderWidth'] = 0.2
        return default_opt

    def get_dataset_configs(self):
        datasets = []
        color_generator = self.get_color_iterator()
        data = self.get_datasets()
        dataset_labels = self.get_dataset_labels()
        num = len(dataset_labels)
        for i, entry in enumerate(data):
            color = tuple(next(color_generator))
            dataset = {"data": entry}
            dataset.update(self.get_dataset_options(i, color))
            if i < num:
                dataset["label"] = dataset_labels[i]  # series labels for Chart.js
                dataset["name"] = dataset_labels[i]  # HighCharts may need this
            datasets.append(dataset)
        return datasets


class StackedBarChart(BarChart):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_stacked(True)


class HorizontalBarChart(BarChart):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_horizontal(True)


class HorizontalStackedBarChart(BarChart):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_horizontal(True)
        self.set_stacked(True)


class Histogram(BarChart):

    def __init__(self, *args, **kwargs):
        if "histogram" not in kwargs:
            kwargs["histogram"] = True
        super().__init__(*args, **kwargs)

    def build(self, data, bin_count):
        num_min = min(data)
        num_max = max(data)

        num_range = num_max - num_min
        bin_chunk = num_range / bin_count
        bin_power = math.floor(math.log10(bin_chunk))
        bin_chunk = math.ceil(bin_chunk / 10**bin_power) * 10**bin_power
        if num_min < 0:
            bin_min = math.ceil(math.fabs(num_min / bin_chunk)) * bin_chunk * -1
        else:
            bin_min = math.floor(num_min / bin_chunk) * bin_chunk
        if num_max < 0:
            bin_max = math.floor(math.fabs(num_max / bin_chunk)) * bin_chunk * -1
        else:
            bin_max = math.ceil(num_max / bin_chunk) * bin_chunk
        categories = list(range(bin_min, bin_max + bin_chunk, bin_chunk))
        self.set_option('max', categories[-2])
        self.set_option('histogram_max', categories[-1])
        bins = [0] * bin_count
        for num in data:
            for i in range(len(categories) - 1):
                if num >= categories[i] and num < categories[i + 1]:
                    if i < len(bins):
                        bins[i] += 1
        self.set_categories(categories)
        self.add_dataset(bins, 'data')


class HorizontalHistogram(Histogram):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_horizontal(True)
