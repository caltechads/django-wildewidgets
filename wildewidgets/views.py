import base64
import importlib
import json
import os

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.utils.cache import add_never_cache_headers
try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_str as force_text  # type: ignore
from django.utils.functional import Promise
from django.views.generic import View
from django.views.generic.base import TemplateView


class LazyEncoder(DjangoJSONEncoder):
    """Encodes django's lazy i18n strings
    """
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_text(obj)
        return super(LazyEncoder, self).default(obj)


# =================================
# Mixins
# =================================

class WidgetInitKwargsMixin:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
            for k, v in extra_item.items():
                extra_list.append(f"{k}={v}")
            extra = f"{start}{'&'.join(extra_list)}"
            return extra
        return ''


class JSONResponseMixin:
    is_clean = False

    def render_to_response(self, context):
        """ Returns a JSON response containing 'context' as payload
        """
        return self.get_json_response(context)

    def get_json_response(self, content, **httpresponse_kwargs):
        """ Construct an `HttpResponse` object.
        """
        response = HttpResponse(content,
                                content_type='application/json',
                                **httpresponse_kwargs)
        add_never_cache_headers(response)
        return response

    def post(self, *args, **kwargs):
        return self.get(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.request = request
        self.csrf_token = self.request.GET.get('csrf_token', None)
        response = None

        func_val = self.get_context_data(**kwargs)
        if not self.is_clean:
            assert isinstance(func_val, dict)
            response = dict(func_val)
            if 'error' not in response and 'sError' not in response:
                response['result'] = 'ok'
            else:
                response['result'] = 'error'
        else:
            response = func_val
        # can't have 'view' here, because the view object can't be jsonified
        junk = response.pop('view', None)

        dump = json.dumps(response, cls=LazyEncoder)
        return self.render_to_response(dump)


# =================================
# Views
# =================================


class JSONResponseView(JSONResponseMixin, TemplateView):
    pass


class JSONDataView(View):

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        return {}

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context)


class WildewidgetDispatch(WidgetInitKwargsMixin, View):

    def dispatch(self, request, *args, **kwargs):
        # initkwargs = {}

        wildewidgetclass = request.GET.get('wildewidgetclass', None)
        csrf_token = request.GET.get('csrf_token', '')
        if wildewidgetclass:
            configs = apps.get_app_configs()
            for config in configs:
                check_file = os.path.join(config.path, "wildewidgets.py")
                check_dir = os.path.join(config.path, "wildewidgets")
                if os.path.isfile(check_file) or os.path.isdir(check_dir):
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


class TableActionFormView(View):
    http_method_names = ['post']
    url = None

    def process_form_action(self, action, items):
        pass

    def post(self, request, *args, **kwargs):
        checkboxes = request.POST.getlist('checkbox')
        action = request.POST.get('action')
        self.process_form_action(action, checkboxes)
        return HttpResponseRedirect(self.url)


class TableView(TemplateView):
    table_class = None

    def get_context_data(self, **kwargs):
        if not self.table_class:
            raise ImproperlyConfigured(
                "You must set a table_class attribute on {}".format(self.__class__.__name__)
            )
        kwargs['table'] = self.table_class()
        return super().get_context_data(**kwargs)


class StandardWidgetMixin():

    def get_context_data(self, **kwargs):
        kwargs['content'] = self.get_content()
        breadcrumbs = self.get_breadcrumbs()
        kwargs['breadcrumbs'] = breadcrumbs
        if breadcrumbs:
            kwargs['page_title'] = breadcrumbs.flatten()
        return super().get_context_data(**kwargs)

    def get_content(self):
        raise ImproperlyConfigured(
                "You must override get_content in {}".format(self.__class__.__name__)
            )
        return None

    def get_breadcrumbs(self):
        return None
