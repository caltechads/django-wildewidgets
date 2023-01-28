import importlib
import os

from django.apps import apps
from django.http import JsonResponse
from django.views.generic import View
from django.views.generic.base import TemplateView

from .mixins import WidgetInitKwargsMixin, JSONResponseMixin


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
