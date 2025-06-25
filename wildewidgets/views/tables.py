from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.core.exceptions import ImproperlyConfigured
from django.http import Http404, HttpResponseRedirect
from django.views.generic import View
from django.views.generic.base import TemplateView

if TYPE_CHECKING:
    from django.http import HttpRequest

    from ..widgets import BaseDataTable


class TableActionFormView(View):
    """
    A view that processes form actions submitted from a data table.

    This view handles POST requests containing table actions (like bulk delete,
    approve, etc.) and delegates the processing to action-specific methods. It
    follows a convention-based approach where actions are processed by methods
    named `process_{action}_action`.

    To use this view:

    1. Subclass it and implement methods for each action (e.g., `process_delete_action`)
    2. Set the `url` attribute to specify where to redirect after processing
    3. Map the view to a URL in your URLconf

    Example:
        .. code-block:: python

            from django.http import HttpResponseRedirect
            from django.urls import reverse_lazy
            from django.views.generic import View
            from wildewidgets import TableActionFormView

            from myapp.models import User

            class UserBulkActionView(TableActionFormView):
                url = reverse_lazy('user-list')

                def process_delete_action(self, items):
                    User.objects.filter(id__in=items).delete()

                def process_activate_action(self, items):
                    User.objects.filter(id__in=items).update(is_active=True)

    """

    #: The HTTP methods this view will respond to
    http_method_names: list[str] = ["post"]  # noqa: RUF012
    #: The URL to redirect to after processing the form action
    url: str | None = None

    def process_form_action(self, action: str, items: list[str]) -> None:
        """
        Process a form action by delegating to an action-specific method.

        This method looks for a method named `process_{action}_action` and calls
        it with the list of selected items. If no such method exists, the action
        is silently ignored.

        Args:
            action: The name of the action to process (e.g., "delete", "approve")
            items: List of item IDs that the action should be applied to

        Example:
            If `action` is "delete", this method will try to call
            `self.process_delete_action(items)`

        """
        method_name = f"process_{action}_action"
        if hasattr(self, method_name):
            getattr(self, method_name)(items)

    def post(
        self,
        request: HttpRequest,
        *args: Any,  # noqa: ARG002
        **kwargs: Any,  # noqa: ARG002
    ) -> HttpResponseRedirect | Http404:
        """
        Handle POST requests by processing the form action and redirecting.

        This method:

        1. Extracts the selected items and action from the POST data
        2. Delegates to `process_form_action` for the actual processing
        3. Redirects to the URL specified by the `url` attribute

        Args:
            request: The HTTP request object
            *args: Additional positional arguments (not used)
            **kwargs: Additional keyword arguments (not used)

        Returns:
            HttpResponseRedirect: Redirect to the specified URL after successful
                processing
            Http404: If the request doesn't include required POST data

        Raises:
            ImproperlyConfigured: If the `url` attribute is not set

        """
        checkboxes = request.POST.getlist("checkbox")
        action = request.POST.get("action")
        if not action or not checkboxes:
            return Http404("POST request did not include the necessary fields")
        self.process_form_action(action, checkboxes)
        if not self.url:
            msg = f"You must set a url attribute on {self.__class__.__name__}"
            raise ImproperlyConfigured(msg)
        return HttpResponseRedirect(self.url)


class TableView(TemplateView):
    """
    A template view that renders a data table.

    This view simplifies the common pattern of rendering a template that includes
    a data table. It instantiates the specified table class and adds it to the
    template context.

    To use this view:
    1. Subclass it and set the `table_class` attribute to your table class
    2. Set `template_name` to the template that will render the table

    Attributes:
        table_class: The table widget class to instantiate and render

    Example:
        .. code-block:: python

            from wildewidgets import TableView, BaseModelTable
            from myapp.models import User

            class UserTable(BaseModelTable):
                model = User
                fields: List[str] = ["username", "email", "date_joined"]

            class UserTableView(TableView):
                table_class = UserTable

    """

    #: The table class to use for rendering the table.
    table_class: type[BaseDataTable] | None = None

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Add the instantiated table to the template context.

        This method instantiates the table specified by `table_class` and adds
        it to the template context with the key 'table'.

        Args:
            **kwargs: Additional context variables

        Returns:
            dict: The updated template context with the table instance

        Raises:
            ImproperlyConfigured: If `table_class` is not set

        """
        if not self.table_class:
            msg = f"You must set a table_class attribute on {self.__class__.__name__}"
            raise ImproperlyConfigured(msg)
        kwargs["table"] = self.table_class()  # pylint: disable=not-callable
        return super().get_context_data(**kwargs)
