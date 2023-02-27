from typing import Any, Dict, Optional, TYPE_CHECKING
import base64
import json

from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.utils.cache import add_never_cache_headers
try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_str as force_text  # type: ignore
from django.utils.functional import Promise

if TYPE_CHECKING:
    from ..widgets import BreadcrumbBlock


class LazyEncoder(DjangoJSONEncoder):
    """
    Encodes django's lazy i18n strings.
    """
    def default(self, o):
        if isinstance(o, Promise):
            return force_text(o)
        return super(LazyEncoder, self).default(o)


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
        if isinstance(extra_item, dict):
            extra_list = []
            for k, v in extra_item.items():
                extra_list.append(f"{k}={v}")
            extra = f"{start}{'&'.join(extra_list)}"
            return extra
        return ''


class JSONResponseMixin:

    is_clean: bool = False

    def render_to_response(self, context: Dict[str, Any]) -> str:
        """
        Returns a JSON response containing 'context' as payload
        """
        return self.get_json_response(context)

    def get_json_response(self, content: Any, **httpresponse_kwargs) -> HttpResponse:
        """
        Construct an `HttpResponse` object.
        """
        response = HttpResponse(
            content,
            content_type='application/json',
            **httpresponse_kwargs
        )
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
        response.pop('view', None)

        dump = json.dumps(response, cls=LazyEncoder)
        return self.render_to_response(dump)


class StandardWidgetMixin:
    """
    A class based view mixin for views that use a standard widget template.
    This is used with a template-less design.

    The template used by your derived class should include at least the following::

        {% extends "<your_base_template>.html" %}
        {% load  wildewidgets %}

        {% block title %}{{page_title}}{% endblock %}

        {% block breadcrumb-items %}
        {% if breadcrumbs %}
            {% wildewidgets breadcrumbs %}
        {% endif %}
        {% endblock %}

        {% block content %}
        {% wildewidgets content %}
        {% endblock %}

    The ``content`` block is where the content of the page is rendered. The
    ``breadcrumbs`` block is where the breadcrumbs are rendered.

    An example derived class, which will be used by most of the views in the project::

        class DemoStandardMixin(StandardWidgetMixin, NavbarMixin):
            template_name='core/standard.html'
            menu_class = DemoMenu

    The ``DemoStandardMixin`` class is used in the following way::

        class HomeView(DemoStandardMixin, TemplateView):
            menu_item = 'Home'

            def get_content(self):
                return HomeBlock()

            def get_breadcrumbs(self):
                breadcrumbs = DemoBaseBreadcrumbs()
                breadcrumbs.add_breadcrumb('Home')
                return breadcrumbs
    """

    def get_context_data(self, **kwargs):
        kwargs['content'] = self.get_content()
        breadcrumbs: "Optional[BreadcrumbBlock]" = self.get_breadcrumbs()
        if breadcrumbs:
            kwargs['breadcrumbs'] = breadcrumbs
            kwargs['page_title'] = breadcrumbs.flatten()
        return super().get_context_data(**kwargs)

    def get_content(self):
        raise NotImplementedError(
            f"You must override get_content in {self.__class__.__name__}"
        )

    def get_breadcrumbs(self) -> "Optional[BreadcrumbBlock]":
        return None
