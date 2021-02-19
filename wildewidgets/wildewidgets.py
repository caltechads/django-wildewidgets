from functools import lru_cache
import importlib
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

try: 
    from django_datatables_view.base_datatable_view import BaseDatatableView
    datatables_is_defined = True
except ModuleNotFoundError:
    datatables_is_defined = False


class JSONDataView(View):

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        return {}

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context)


class WildewidgetDispatch(View):

    def dispatch(self, request, *args, **kwargs):
        wildewidgetclass = request.GET.get('wildewidgetclass', None)
        if wildewidgetclass:
            configs = apps.get_app_configs()
            for config in configs:
                check_file = os.path.join(config.path, "wildewidgets.py")
                if os.path.isfile(check_file):
                    module = importlib.import_module(f"{config.name}.wildewidgets")
                    if hasattr(module, wildewidgetclass):
                        class_ = getattr(module, wildewidgetclass)
                        view = class_.as_view()
                        return view(request, *args, **kwargs)


class CategoryChart(JSONDataView):

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

    def get_content(self):
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

    def get_content(self):
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

if datatables_is_defined:
    class DatatableAJAXView(BaseDatatableView):
        """
        This is a JSON view that a DataTables.js table can hit as for its AJAX queries.
        """

        def columns(self, querydict):
            """
            Parse the request we got from the DataTables AJAX request (``querydict``) from a list of strings to a more
            useful nested dict.  We'll use this to more readily figure out what we need to be doing.

            A single column's data in the querystring we got from datatables looks like:

                {
                    'columns[4][data]': 'employee_number',
                    'columns[4][name]': '',
                    'columns[4][orderable]': 'true',
                    'columns[4][search][regex]': 'false',
                    'columns[4][search][value]': '',
                    'columns[4][searchable]': 'true'
                }

            Turn all such data into a dict that looks like:

                {
                    'employee_number': {
                        'column_number': 4,
                        'data': 'employee_number',
                        'name': '',
                        'orderable': True,
                        'search': {
                            'regex': False,
                            'value': ''
                        },
                        'searchable': True
                    }
                }

            :param querydict: dict of all key, value pairs from the ajax request.
            :type querydict: dict

            :rtype: dict
            """
            by_number = {}
            for key, value in querydict.items():
                if value == 'true':
                    value = True
                elif value == 'false':
                    value = False
                if key.startswith('columns'):
                    parts = key.split('[')
                    column_number = parts[1][:-1]
                    column_attribute = parts[2][:-1]
                    if column_number not in by_number:
                        by_number[column_number] = {
                            'column_number': int(column_number)
                        }
                    if len(parts) == 4:
                        if column_attribute not in by_number[column_number]:
                            by_number[column_number][column_attribute] = {parts[3][:-1]: value}
                        else:
                            by_number[column_number][column_attribute][parts[3][:-1]] = value
                    else:
                        by_number[column_number][column_attribute] = value
            # Now make the real lookup be by column name
            by_name = {}
            for key in by_number:
                # 'data' is the column name
                by_name[by_number[key]['data']] = by_number[key]
            return by_name

        @lru_cache(maxsize=4)
        def searchable_columns(self):
            """
            Return the list of all column names from out DataTable that are marked as "searchable"

            :rtype: list of strings
            """
            return [key for key, value in self.columns(self._querydict).items() if value['searchable']]

        def column_specific_searches(self):
            """
            Look through the request data we got from the DataTable AJAX request for any single-column
            searches.  These will look like ``column[$number][search][value]`` in the request.

            :rtype: list of 2-tuples (str, str): (column name, search string)
            """
            return [
                (key, value['search']['value'])
                for key, value in self.columns(self._querydict).items()
                if value['search']['value']
            ]

        def single_column_filter(self, qs, column, value):
            """
            Filter our queryset by a single column.  Columns will be searched by ``__icontains``.

            This gets executed when someone runs a search on a single DataTables.js column::

                data_table.column($number).search($search_string);

            If you want to implement a different search filter for a particular column, add a
            ``search_COLUMN_column(self, qs, column, value)`` method that returns a QuerySet
            to your subclass and that will be called instead.  Example::

                def search_foobar_column(self, qs, column, value):
                    if value == 'something':
                        qs = qs.filter(foobar__attribute=True)
                    elif value == 'other_thing':
                        qs = qs.filter(foobar__other_attribute=False)
                    return qs

            :param qs: the Django QuerySet
            :type qs: QuerySet

            :param column : the dataTables data attribute for the column we're interested in
            :type column: str

            :param value: the search string
            :type value: str

            :rtype: QuerySet
            """
            attr_name = 'search_{}_column'.format(column)
            if hasattr(self, attr_name):
                qs = getattr(self, attr_name)(qs, column, value)
            elif column in self.searchable_columns():
                kwarg_name = '{}__icontains'.format(column)
                qs = qs.filter(**{kwarg_name: value})
            return qs

        def search_query(self, qs, value):
            # 2020-08-05 rrollins TODO: This is very likely wrong. It doesn't use qs at all, and doesn't return a QuerySet.
            """
            Return an ORed Q() object that will search the searchable fields for ``value``

            :param qs: the Django QuerySet
            :type qs: QuerySet

            :param value: the search string
            :type value: str

            :rtype: Q() object
            """
            query = None
            for column in self.searchable_columns():
                kwarg_name = '{}__icontains'.format(column)
                q = Q(**{kwarg_name: value})
                query = query | q if query else q
            return query

        def search(self, qs, value):
            """
            Filter our queryset across all of our searchable columns for ``value``.

            This gets executed when someone runs a search over the whole DataTables.js table::

                data_table.search($search_string);

            This is what happens when the user uses the Search input on the DataTable.

            :param qs: the Django QuerySet
            :type qs: QuerySet

            :param value: the search string
            :type value: str

            :rtype: QuerySet
            """
            query = self.search_query(qs, value)
            qs = qs.filter(query).distinct()
            return qs

        def filter_queryset(self, qs):
            """
            We're overriding the default filter_queryset(method) here so we can implement proper searches on our
            pseudo-columns "responded" and "disabled", and do column specific searches, as well as doing
            general searches across our regular CharField columns.
            """
            column_searches = self.column_specific_searches()
            if column_searches:
                for column, value in column_searches:
                    qs = self.single_column_filter(qs, column, value)
            value = self.request.GET.get('search[value]', None)
            if value:
                qs = self.search(qs, value)
            return qs

        def _render_column(self, row, column):
            """
            When defining our DataTable config, we declare DataTable columns that access columns of models of foreign keys
            on our model with ``__`` notation.  Convert the ``__`` to ``.`` before trying to render the data so
            that things will work correctly.


            :param row: A Django model instance
            :param column: the name of the column to render

            :rtype: string
            """
            column = re.sub('__', '.', column)
            return super()._render_column(row, column)

        def render_column(self, row, column):
            """
            Return the data to add to the DataTable for column ``column`` of the table row corresponding to
            the model object ``row``.

            If you want to implement special rendering a particular column (for instance to display something about an
            object that doesn't map directly to a model column), add a ``render_COLUMN_column(self, row, column)`` method
            that returns a string to your subclass and that will be called instead.  Example::

                def render_foobar_column(self, row, column):
                    return 'some data'

            :param row: A Django model instance
            :param column: the name of the column to render

            :rtype: string
            """
            attr_name = 'render_{}_column'.format(column)
            if hasattr(self, attr_name):
                return getattr(self, attr_name)(row, column)
            else:
                return super().render_column(row, column)


    class DataTableColumn():

        def __init__(self, field, verbose_name=None, searchable=False, sortable=False, align='left', head_align='left', visible=True):
            self.field = field
            if verbose_name:
                self.verbose_name = verbose_name
            else:
                self.verbose_name = field.capitalize()
            self.searchable = searchable
            self.sortable = sortable
            self.align = align
            self.head_align = head_align
            self.visible = visible


    class DataTableFilter():

        def __init__(self, header=None):
            self.header = header
            self.choices = [('Any', '')]

        def add_choice(self, label, value):
            self.choices.append((label, value))
            

    class DataTable(DatatableAJAXView):

        template_file = 'wildewidgets/table.html'

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.options = {
                'width': kwargs.get('width', '400'),
                'height': kwargs.get('height', '400'),
                "title":kwargs.get('title', None),
                "searchable":kwargs.get('searchable', True),
                "paging":kwargs.get('paging', True),
                "page_length":kwargs.get('page_length', None),
            }
            self.table_id = kwargs.get('table_id', None)
            self.column_fields = {}
            self.column_filters = {}
            self.data = []

        def add_column(self, field, verbose_name=None, searchable=True, sortable=True, align='left', head_align='left', visible=True):
            self.column_fields[field] = DataTableColumn(field=field, verbose_name=verbose_name, searchable=searchable, sortable=sortable, align=align, head_align=head_align, visible=visible)

        def add_filter(self, field, filter):
            self.column_filters[field] = filter

        def build_context(self):
            context = {
                'rows':self.data            
            }
            return context

        def get_content(self):
            has_filters = False
            filters = []
            for key, item in self.column_fields.items():
                if key in self.column_filters:
                    filters.append((item, self.column_filters[key]))
                    has_filters = True
                else:
                    filters.append(None)
            if self.table_id:
                table_id = self.table_id
            else:
                table_id = random.randrange(0,1000)
            template_file = self.template_file
            if self.data:
                context = self.build_context()
            else:
                context = {"async":True}
            html_template = template.loader.get_template(template_file)
            context['header'] = self.column_fields
            context['filters'] = filters
            context['has_filters'] = has_filters
            context['options'] = self.options
            context['name'] = f"datatable_table_{table_id}"
            context["tableclass"] = self.__class__.__name__
            content = html_template.render(context)
            return content

        def __str__(self):
            return self.get_content()

        def add_row(self, **kwargs):
            row = []
            for field in self.column_fields.keys():
                if field in kwargs:
                    row.append(kwargs[field])
                else:
                    row.append('')
            self.data.append(row)


class BasicMenu():

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
            subdata = {
                'title':item[0],
                'url':reverse_lazy(item[1]),
                'extra':''
            }

            if len(item) > 2:
                subdata['extra'] = self._get_extra(item[2])
            sub_menu_items.append(subdata)

        data['items'] = sub_menu_items
        return data

    def _get_extra(self, extra_item):
        if type(extra_item) == dict:
            extra_list = []
            for k,v in extra_item.items():
                extra_list.append(f"{k}={v}")
            extra = f"?{'&'.join(extra_list)}"
            return extra
        return ''

    def get_content(self):
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
