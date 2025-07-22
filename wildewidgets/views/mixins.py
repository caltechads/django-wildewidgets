from __future__ import annotations

import base64
import json
from typing import TYPE_CHECKING, Any

from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.utils.cache import add_never_cache_headers

try:
    from django.utils.encoding import force_text  # type: ignore[import]
except ImportError:
    from django.utils.encoding import force_str as force_text
from django.utils.functional import Promise

if TYPE_CHECKING:
    from django.http import HttpRequest

    from ..widgets import BreadcrumbBlock


class LazyEncoder(DjangoJSONEncoder):
    """
    Custom JSON encoder that handles Django's lazy i18n translation strings.

    This encoder extends Django's built-in JSON encoder to properly serialize
    lazy translation strings (Promise objects) by forcing them to text before
    encoding.

    Examples:
        .. code-block:: python

            data = {'message': _('Hello World')}
            json_data = json.dumps(data, cls=LazyEncoder)

    """

    def default(self, o: Any) -> Any:
        """
        Convert the given object to a JSON serializable type.

        Args:
            o: Object to be serialized

        Returns:
            A JSON serializable version of the object

        """
        if isinstance(o, Promise):
            return force_text(o)
        return super().default(o)


class WidgetInitKwargsMixin:
    """
    Mixin that preserves widget initialization arguments for AJAX requests.

    This mixin stores widget initialization arguments and provides methods
    to encode them for transmission in URLs and decode them from HTTP requests.
    This allows widgets to preserve their state between initial rendering and
    subsequent AJAX calls.

    The mixin stores both positional and keyword arguments and can serialize
    them to base64-encoded JSON for inclusion in URLs or form data.  The way
    it does it is as follows:

    - We make a dictionary
    - The positional arguments are stored in the "args" key.
    - The keyword arguments are stored in the "kwargs" key.
    - The resulting dictionary is then serialized to JSON and encoded as
      base64 for transmission.
    - The :py:meth:`get_encoded_extra_data` method returns the base64-encoded
      JSON string that can be included in URLs or form data.
    - The :py:meth:`get_decoded_extra_data(request)` method decodes the base64 string
      from the request and returns the original arguments as a dictionary.

    The encoded data can be used in AJAX requests as the ``extra_data`` query
    parameter to reconstruct the widget's state without needing to pass all
    arguments explicitly in the request.

    This is primarily used by :py:class:`wildewidgets.WildewidgetDispatch` to
    pass widget initialization arguments to tables and other widgets that
    require them for rendering or processing AJAX requests.

    Examples:
        .. code-block:: python

            from wildewidgets import WidgetInitKwargsMixin, Widget

            class MyWidget(WidgetInitKwargsMixin, Widget):
                def __init__(self, user_id, show_details=False, **kwargs):
                    super().__init__(user_id, show_details=show_details, **kwargs)
                    # The args and kwargs are now stored in self.extra_data

    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the mixin and store initialization arguments.

        Args:
            *args: Positional arguments to preserve
            **kwargs: Keyword arguments to preserve

        """
        super().__init__(*args, **kwargs)
        self.extra_data = {"args": args, "kwargs": kwargs}

    def get_encoded_extra_data(self):
        """
        Encode widget initialization arguments as base64 for URL transmission.

        This method serializes the stored arguments to JSON, encodes them as
        base64, and returns them as a string that can be included in URLs.

        Returns:
            str: Base64-encoded JSON string of the initialization arguments

        """
        data_json = json.dumps(self.extra_data)
        payload_bytes = base64.b64encode(data_json.encode())
        return payload_bytes.decode()

    def get_decoded_extra_data(self, request):
        """
        Decode widget initialization arguments from an HTTP request.

        This method extracts the "extra_data" parameter from the request's
        GET parameters, decodes it from base64, and parses it as JSON.

        Args:
            request: The HTTP request containing encoded widget arguments

        Returns:
            dict: Decoded initialization arguments (empty dict if none found)

        """
        encoded_extra_data = request.GET.get("extra_data", None)
        if not encoded_extra_data:
            return {}
        extra_bytes = encoded_extra_data.encode()
        payload_bytes = base64.b64decode(extra_bytes)
        return json.loads(payload_bytes.decode())

    def convert_extra(self, extra_item, first=True):
        """
        Convert extra data to URL query string format.

        This method formats a dictionary as URL query parameters, either
        starting with "?" (if first=True) or "&" (if first=False).

        Args:
            extra_item: Dictionary of parameters to convert
            first: Whether this is the first set of parameters in a URL

        Returns:
            str: Formatted URL query string segment

        """
        start = "?" if first else "&"
        if isinstance(extra_item, dict):
            extra_list = []
            for k, v in extra_item.items():
                extra_list.append(f"{k}={v}")
            return f"{start}{'&'.join(extra_list)}"
        return ""


class JSONResponseMixin:
    """
    Mixin that provides JSON response handling for views.

    This mixin allows views to return JSON responses by converting the context
    data from get_context_data() into a JSON string and returning it with the
    appropriate content type. It also handles adding standard result indicators
    and removing non-serializable view objects.

    Attributes:
    Examples:
        .. code-block:: python

            from django.utils import timezone
            from django.views import View
            from wildewidgets import JSONResponseMixin

            def get_some_data():
                return {"key": "value", "another_key": 42}

            class MyJSONView(JSONResponseMixin, View):
                def get_context_data(self, **kwargs):
                    return {
                        'data': get_some_data(),
                        'timestamp': timezone.now().isoformat()
                    }

    """

    #: If True, return context data as-is without adding a
    #: "result" field. If False, add "result": "ok" or
    #: "result": "error" based on the presence of error indicators.
    is_clean: bool = False

    def render_to_response(self, data: str) -> HttpResponse:
        """
        Return a JSON response containing the provided data.

        Args:
            data: JSON string to include in the response

        Returns:
            HttpResponse: HTTP response with JSON content type

        """
        return self.get_json_response(data)

    def get_json_response(self, content: Any, **httpresponse_kwargs) -> HttpResponse:
        """
        Create a properly configured HttpResponse with JSON content type.

        This method creates an HttpResponse with the provided content and
        sets the content type to "application/json". It also adds cache
        control headers to prevent caching of the response.

        Args:
            content: The content to include in the response
            **httpresponse_kwargs: Additional keyword arguments for HttpResponse

        Returns:
            HttpResponse: Configured HTTP response with JSON content

        """
        response = HttpResponse(
            content, content_type="application/json", **httpresponse_kwargs
        )
        add_never_cache_headers(response)
        return response

    def post(self, *args, **kwargs) -> HttpResponse:
        """
        Handle POST requests by delegating to the GET handler.

        This allows the same JSON response logic to be used for both
        GET and POST requests.

        Args:
            *args: Positional arguments to pass to get()
            **kwargs: Keyword arguments to pass to get()

        Returns:
            HttpResponse: JSON response from get() method

        """
        return self.get(*args, **kwargs)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:  # noqa: ARG002
        """
        Handle GET requests by returning a JSON response.

        This method:

        1. Processes the request to extract the CSRF token
        2. Gets context data from get_context_data()
        3. Adds a "result" field if not in clean mode
        4. Removes non-serializable view object
        5. Serializes to JSON and returns the response

        Args:
            request: The HTTP request
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            HttpResponse: HTTP response with JSON content

        Raises:
            AssertionError: If get_context_data() doesn't return a dictionary

        """
        self.request: HttpRequest = request
        self.csrf_token: str | None = self.request.GET.get("csrf_token", None)
        response: dict[str, Any] | None = None

        func_val = self.get_context_data(**kwargs)  # type: ignore[attr-defined]
        assert isinstance(func_val, dict), "get_context_data must return a dict"  # noqa: S101
        if not self.is_clean:
            response = dict(func_val)
            if "error" not in response and "sError" not in response:
                response["result"] = "ok"
            else:
                response["result"] = "error"
        else:
            response = func_val
        # can't have 'view' here, because the view object can't be jsonified
        response.pop("view", None)

        dump = json.dumps(response, cls=LazyEncoder)
        return self.render_to_response(dump)


class StandardWidgetMixin:
    """
    A mixin for views that use a standard widget-based template structure.

    This mixin provides a convention for template-less views that render their
    content using widgets. It automatically adds the content widget and optional
    breadcrumbs widget to the template context.

    To use this mixin:
    1. Override :py:meth:`get_content` to return the main content widget
    2. Optionally override :py:meth:`get_breadcrumbs` to provide breadcrumb navigation
    3. Ensure your template includes the necessary blocks and loads the
       wildewidgets template tags

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

    Examples:
        Basic view using the StandardWidgetMixin:

        .. code-block:: python

            from django.views.generic import TemplateView
            from wildewidgets.views.mixins import StandardWidgetMixin
            from wildewidgets import Block, BreadcrumbBlock

            class HomeContentWidget(Block):
                block = "home-content"
                tag = "h1"

                def __init__(self, user):
                    super().__init__(f"Welcome, {user.username}!")


            class AppBreadcrumbs(BreadcrumbBlock):
                def __init__(self):
                    super().__init__()
                    self.add_breadcrumb('Home', url='/')


            class HomeView(StandardWidgetMixin, TemplateView):
                template_name = 'myapp/standard.html'

                def get_content(self):
                    return HomeContentWidget(user=self.request.user)

                def get_breadcrumbs(self):
                    breadcrumbs = AppBreadcrumbs()
                    breadcrumbs.add_breadcrumb('Home')
                    return breadcrumbs

    """

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Add content widget and breadcrumbs to the template context.

        This method:
        1. Gets content widget from get_content()
        2. Gets optional breadcrumbs widget from get_breadcrumbs()
        3. If breadcrumbs exist, adds them and sets page_title
        4. Delegates to parent class for additional context

        Args:
            **kwargs: Additional context variables

        Returns:
            dict: The updated template context

        """
        kwargs["content"] = self.get_content()
        breadcrumbs: BreadcrumbBlock | None = self.get_breadcrumbs()
        if breadcrumbs:
            kwargs["breadcrumbs"] = breadcrumbs
            kwargs["page_title"] = breadcrumbs.flatten()
        return super().get_context_data(**kwargs)  # type: ignore[misc]

    def get_content(self):
        """
        Get the main content widget for the page.

        This method must be overridden by subclasses to provide the
        widget that will be rendered in the content block.

        Returns:
            Widget: The main content widget

        Raises:
            NotImplementedError: If not overridden by subclass

        """
        msg = f"You must override get_content in {self.__class__.__name__}"
        raise NotImplementedError(msg)

    def get_breadcrumbs(self) -> BreadcrumbBlock | None:
        """
        Get the breadcrumbs widget for the page.

        Override this method to provide breadcrumb navigation. By default,
        no breadcrumbs are shown.

        Returns:
            BreadcrumbBlock | None: Breadcrumb widget or None if no breadcrumbs

        """
        return None
