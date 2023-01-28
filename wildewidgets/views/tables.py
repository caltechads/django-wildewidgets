from typing import List, Optional, Type, TYPE_CHECKING

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseRedirect
from django.views.generic import View
from django.views.generic.base import TemplateView

if TYPE_CHECKING:
    from ..widgets import BaseDataTable


class TableActionFormView(View):
    """
    A view that handles a form action on a table. You just need to define the :py:meth:`process_form_action` method.
    """

    http_method_names: List[str] = ['post']
    url: Optional[str] = None

    def process_form_action(self, action: str, items: List[str]) -> None:
        method_name = f'process_{action}_action'
        if hasattr(self, method_name):
            getattr(self, method_name)(items)

    def post(self, request, *args, **kwargs):
        checkboxes = request.POST.getlist('checkbox')
        action = request.POST.get('action')
        self.process_form_action(action, checkboxes)
        return HttpResponseRedirect(self.url)


class TableView(TemplateView):

    table_class: "Optional[Type[BaseDataTable]]" = None

    def get_context_data(self, **kwargs):
        if not self.table_class:
            raise ImproperlyConfigured(
                f"You must set a table_class attribute on {self.__class__.__name__}"
            )
        kwargs['table'] = self.table_class()  # pylint: disable=not-callable
        return super().get_context_data(**kwargs)
