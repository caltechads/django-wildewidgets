from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from django.apps import apps
from django.http import Http404, HttpRequest, HttpResponseBase, JsonResponse
from django.views.generic import View
from django.views.generic.base import TemplateView

from .mixins import JSONResponseMixin, WidgetInitKwargsMixin


class JSONResponseView(JSONResponseMixin, TemplateView):  # type: ignore[misc]
    """
    A view that renders a template and returns the result as a JSON response.

    This view combines Django's TemplateView with JSONResponseMixin to provide a
    simple way to return template-rendered content within a JSON response. This
    is useful for AJAX requests that need to return HTML fragments within a JSON
    structure.

    When subclassing, you typically need to override the template_name attribute
    and optionally the get_context_data method.

    Attributes:
        template_name: The template to render (must be set by subclasses)

    Example:
        .. code-block:: python

            class MyJSONView(JSONResponseView):
                template_name = "my_template.html"

                def get_context_data(self, **kwargs):
                    context = super().get_context_data(**kwargs)
                    context['extra_data'] = get_some_data()
                    return context

    """


class JSONDataView(View):
    """
    A view that returns JSON data in response to HTTP requests.

    This class provides a simple framework for views that need to return JSON data.
    It handles the HTTP request/response cycle and serializes the context data
    to JSON. By default, it only responds to GET requests.

    To use this class, subclass it and override the get_context_data method to
    provide the data you want to return as JSON.

    Example:
        .. code-block:: python

            class UserDataView(JSONDataView):
                def get_context_data(self, **kwargs):
                    user_id = self.kwargs.get('user_id')
                    user = User.objects.get(id=user_id)
                    return {
                        'username': user.username,
                        'email': user.email,
                        'date_joined': user.date_joined.isoformat()
                    }

    """

    def get(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:  # noqa: ARG002
        """
        Handle GET requests by returning JSON data.

        This method retrieves the context data and returns it as a JSON response.

        Args:
            request: The HTTP request object
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            JsonResponse: HTTP response containing the JSON-serialized context data

        """
        context = self.get_context_data()
        return self.render_to_response(context)

    def get_context_data(self, **kwargs) -> dict[str, Any]:  # noqa: ARG002
        """
        Get the data to include in the JSON response.

        Override this method to provide the data you want to include in the response.
        By default, it returns an empty dictionary.

        Args:
            **kwargs: Additional context data

        Returns:
            dict: The data to serialize to JSON

        """
        return {}

    def render_to_response(self, context, **response_kwargs) -> JsonResponse:  # noqa: ARG002
        """
        Create a JSON response from the context data.

        This method serializes the context data to JSON and returns it as an
        HTTP response.

        Args:
            context: The data to serialize to JSON
            **response_kwargs: Additional response parameters (unused)

        Returns:
            JsonResponse: HTTP response containing the JSON-serialized context data

        """
        return JsonResponse(context)


class WildewidgetDispatch(WidgetInitKwargsMixin, View):
    """
    A view that dynamically dispatches requests to widget classes.

    This view acts as a central dispatcher for widget AJAX requests. It examines
    the request parameters to determine which widget class to instantiate, then
    delegates the request handling to that widget's dispatch method.

    The view searches for widget classes in all installed Django apps by looking
    for a 'wildewidgets.py' file or a 'wildewidgets' directory within each app.

    This approach allows widgets to handle their own AJAX requests without
    requiring explicit URL routing for each widget type.

    Example usage in URLs:
        .. code-block:: python

            path(
                'wildewidget/',
                WildewidgetDispatch.as_view(),
                name='wildewidget_dispatch'
            )

    Example client-side code:
        .. code-block:: javascript

            $.ajax({
                url: '/wildewidget/',
                data: {
                    'wildewidgetclass': 'MyWidget',
                    'extra_data': encodeURIComponent(JSON.stringify({
                        args: [],
                        kwargs: {param1: 'value1'}
                    }))
                }
            });
    """

    def dispatch(  # type: ignore[override]
        self, request: HttpRequest, *args, **kwargs
    ) -> HttpResponseBase | Http404:
        """
        Dispatch the request to the appropriate widget class.

        This method:

        1. Extracts the widget class name from the request
        2. Searches for the widget class in all installed apps
        3. Instantiates the widget class with the provided arguments
        4. Delegates to the widget's dispatch method

        Args:
            request: The HTTP request object
            *args: Additional positional arguments

        Keyword Arguments:
            **kwargs: Additional keyword arguments

        Returns:
            HttpResponseBase: The response from the widget's dispatch method
            Http404: If the widget class cannot be found

        Note:
            The request must include:
            - 'wildewidgetclass': The name of the widget class to instantiate

            The request may include:
            - 'csrf_token': Optional CSRF token for protected requests
            - 'extra_data': Optional base64 encoded JSON encoded string
              containing a dict with  'args' and 'kwargs' keys for widget
              initialization

        """
        wildewidgetclass = request.GET.get("wildewidgetclass", None)
        csrf_token = request.GET.get("csrf_token", "")
        if wildewidgetclass:
            configs = apps.get_app_configs()
            for config in configs:
                check_file = Path(config.path) / "wildewidgets.py"
                check_dir = Path(config.path) / "wildewidgets"
                if check_file.is_file() or check_dir.is_dir():
                    module = importlib.import_module(f"{config.name}.wildewidgets")
                    if hasattr(module, wildewidgetclass):
                        class_ = getattr(module, wildewidgetclass)
                        extra_data = self.get_decoded_extra_data(request)
                        initargs = extra_data.get("args", [])
                        initkwargs = extra_data.get("kwargs", {})
                        instance = class_(*initargs, **initkwargs)
                        instance.request = request
                        instance.csrf_token = csrf_token
                        instance.args = initargs
                        instance.kwargs = initkwargs
                        return instance.dispatch(request, *args, **kwargs)
        return Http404("Not Found: Wildewidget class not found")
