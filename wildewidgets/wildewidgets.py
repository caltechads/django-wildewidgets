import base64
from functools import lru_cache
import importlib
import json
import math
import os
import random
import re

from django import template
from django.apps import apps
from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import View


class JSONDataView(View):

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        return {}

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context)


class WidgetInitKwargsMixin():

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.extra_data = {
            "args": args,
            "kwargs": kwargs
        }

    def get_encoded_extra_data(self):
        data_json = json.dumps(self.extra_data)
        payload_bytes = base64.b64encode(data_json.encode())
        payload = payload_bytes.decode()
        return payload

    def get_decoded_extra_data(self, request):
        encoded_extra_data = request.GET.get("extra_data", None)
        if not encoded_extra_data:
            return {}
        extra_bytes = encoded_extra_data.encode()
        payload_bytes = base64.b64decode(extra_bytes)
        payload = json.loads(payload_bytes.decode())
        return payload

    def convert_extra(self, extra_item, first=True):
        if first:
            start = '?'
        else:
            start = '&'
        if type(extra_item) == dict:
            extra_list = []
            for k,v in extra_item.items():
                extra_list.append(f"{k}={v}")
            extra = f"{start}{'&'.join(extra_list)}"
            return extra
        return ''


class WildewidgetDispatch(WidgetInitKwargsMixin, View):

    def dispatch(self, request, *args, **kwargs):
        # initkwargs = {}

        wildewidgetclass = request.GET.get('wildewidgetclass', None)
        csrf_token = request.GET.get('csrf_token', '')
        if wildewidgetclass:
            configs = apps.get_app_configs()
            for config in configs:
                check_file = os.path.join(config.path, "wildewidgets.py")
                if os.path.isfile(check_file):
                    module = importlib.import_module(f"{config.name}.wildewidgets")
                    if hasattr(module, wildewidgetclass):
                        class_ = getattr(module, wildewidgetclass)
                        extra_data = self.get_decoded_extra_data(request)
                        initargs = extra_data.get('args', [])
                        initkwargs = extra_data.get('kwargs', {})
                        instance = class_(*initargs, **initkwargs)
                        instance.request = request
                        instance.csrf_token = csrf_token
                        instance.args = initargs
                        instance.kwargs = initkwargs
                        return instance.dispatch(request, *args, **kwargs)


class CategoryChart(WidgetInitKwargsMixin, JSONDataView):

    COLORS = [
        (0,59,76),
        (0,88,80),
        (100,75,120),
        (123,48,62),
        (133,152,148),
        (157,174,136),
        (159,146,94),
        (242,211,131),
        (30,152,138),
        (115,169,80)
    ]

    GRAYS = [
        (200,200,200),
        (229,229,229),
        (170,169,159),
        (118,119,123),
        (97,98,101),
        (175,175,175),
        (105,107,115),
    ]
    template_file = 'wildewidgets/categorychart.html'

    def __init__(self, *args, **kwargs):        
        self.options = {
            'width': kwargs.get('width', '400'),
            'height': kwargs.get('height', '400'),
            "title":kwargs.get('title', None),
            "legend":kwargs.get('legend', False),
            "legend_position":kwargs.get('legend_position', "top"),
            "chart_type":kwargs.get('chart_type',None),
            "histogram":kwargs.get('histogram',False),
            "max":kwargs.get('max',None),
            "thousands":kwargs.get('thousands',False),
            "histogram_max":kwargs.get('histogram_max',None),
            "url":kwargs.get('url',None)
        }
        self.chart_id = kwargs.get('chart_id', None)
        self.categories = None
        self.datasets = []
        self.dataset_labels = []
        self.color = kwargs.get('color', True)
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
            chart_id = random.randrange(0,1000)                
        template_file = self.template_file            
        if self.datasets:
            context = self.get_context_data()
        else:
            context = {"async":True}
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
        if not 'chart_type' in kwargs:
            kwargs['chart_type'] = "doughnut"
        super().__init__(*args, **kwargs)

    def get_dataset_configs(self):
        datasets = []
        color_generator = self.get_color_iterator()
        data = self.get_dataset()
        labels = self.get_categories()
        num = len(labels)
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
        if not "chart_type" in kwargs:
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
        if not "histogram" in kwargs:
            kwargs["histogram"] = True
        super().__init__(*args, **kwargs)

    def build(self, data, bin_count):
        num_min = min(data)
        num_max = max(data)

        num_range = num_max - num_min
        bin_chunk = num_range/bin_count
        bin_power = math.floor(math.log10(bin_chunk))
        bin_chunk = math.ceil(bin_chunk/10**bin_power) * 10**bin_power
        if num_min < 0:
            bin_min = math.ceil(math.fabs(num_min/bin_chunk)) * bin_chunk * -1
        else:
            bin_min = math.floor(num_min/bin_chunk) * bin_chunk
        if num_max < 0:
            bin_max = math.floor(math.fabs(num_max/bin_chunk)) * bin_chunk * -1
        else:
            bin_max = math.ceil(num_max/bin_chunk) * bin_chunk
        categories = list(range(bin_min, bin_max + bin_chunk, bin_chunk))
        self.set_option('max', categories[-2])
        self.set_option('histogram_max', categories[-1])
        bins = [0] * bin_count
        for num in data:
            for i in range(len(categories)-1):
                if num >= categories[i] and num < categories[i+1]:
                    if i < len(bins):
                        bins[i] += 1
        self.set_categories(categories)
        self.add_dataset(bins, 'data')


class HorizontalHistogram(Histogram):

    def __init__(self, *args, **kwargs):        
        super().__init__(*args, **kwargs)
        self.set_horizontal(True)


class AltairChart(JSONDataView):

    template_file = 'wildewidgets/altairchart.html'

    def __init__(self, *args, **kwargs):
        self.data = None
        self.options = {
            'width': kwargs.get('width', '400px'),
            'height': kwargs.get('height', '300px'),
            "title":kwargs.get('title', None)
        }

    def get_content(self, **kwargs):
        chart_id = random.randrange(0,1000)
        template_file = self.template_file
        if self.data:
            context = self.get_context_data()
        else:
            context = {"async":True}
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


class BasicMenu(WidgetInitKwargsMixin):

    template_file = "wildewidgets/menu.html"
    navbar_classes = "navbar-expand-lg navbar-dark bg-secondary"
    items = []

    def __init__(self, *args, **kwargs):
        self.menu= {}
        self.active = None
        if args:
            for item in self.items:
                data = {}
                if type(item[1]) == str:
                    data['url'] = reverse_lazy(item[1])
                    data['extra'] = ''
                    data['kind'] = 'item'

                    if len(item) > 2:
                        extra = item[2]
                        if type(extra) == dict:
                            extra_list = []
                            for k,v in extra.items():
                                extra_list.append(f"{k}={v}")
                            extra = f"?{'&'.join(extra_list)}"
                            data['extra'] = extra
                elif type(item[1]) == list:
                    data = self.parse_submemu(item[1])

                self.add_menu_item(item[0], data, item[0] == args[0])

    def add_menu_item(self, title, data, active=False):
        self.menu[title] = data
        if active:
            self.active = title

    def parse_submemu(self, items):
        data = {
            'kind':'submenu'            
        }
        sub_menu_items = []
        for item in items:
            if not type(item) == tuple:
                continue
            if item[0] == 'divider':
                subdata = {
                    'divider':True
                }
            else:
                subdata = {                    
                    'title':item[0],
                    'url':reverse_lazy(item[1]),
                    'extra':'',
                    'divider':False
                }

            if len(item) > 2:
                subdata['extra'] = self.convert_extra(item[2])
            sub_menu_items.append(subdata)

        data['items'] = sub_menu_items
        return data

    def get_content(self, **kwargs):
        context = {
            'menu':self.menu, 
            'active':self.active,
            'navbar_classes':self.navbar_classes
        }
        html_template = template.loader.get_template(self.template_file)
        content = html_template.render(context)
        return content

    def __str__(self):
        return self.get_content()


class LightMenu(BasicMenu):
    navbar_classes = "navbar-expand-lg navbar-light"


class MenuMixin():
    menu_class = None
    submenu_class = None
    
    def get_menu_class(self):
        if self.menu_class:
            return self.menu_class
        return None
        
    def get_menu(self):
        menu_class = self.get_menu_class()
        if menu_class:
            menu_item = None
            if self.menu_item:
                menu_item = self.menu_item
            return menu_class(self.menu_item)
        return None
        
    def get_submenu_class(self):
        if self.submenu_class:
            return self.submenu_class
        return None
        
    def get_submenu(self):
        submenu_class = self.get_submenu_class()
        if submenu_class:
            submenu_item = None
            if self.submenu_item:
                submenu_item = self.submenu_item
            return submenu_class(submenu_item)
        return None
    
    def get_context_data(self, **kwargs):
        menu = self.get_menu()
        submenu = self.get_submenu()
        if menu:
            kwargs['menu'] = menu
        if submenu:
            kwargs['submenu'] = submenu
        return super().get_context_data(**kwargs)


class TemplateWidget():
    template_name = None
    
    def get_content(self, **kwargs):
        if not self.template_name:
            return None
        context = self.get_context_data(**kwargs)
        html_template = template.loader.get_template(self.template_name)
        content = html_template.render(context)
        return content

    def __str__(self):
        return self.get_content()

    def get_context_data(self, **kwargs):
        return kwargs
    