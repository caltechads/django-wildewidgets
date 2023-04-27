from copy import deepcopy
from typing import Any, Dict, Optional, Type

from django.urls import path
from django.utils.text import slugify
from django.urls import reverse_lazy
from django.views import View

from wildewidgets.views.generic import (
    CreateView,
    DeleteView,
    IndexView,
    UpdateView,
    TableAJAXView,
    TableBulkActionView
)
from wildewidgets.widgets import (
    BaseDataTable,
    BreadcrumbBlock,
    LookupModelTable,
    Navbar
)

from .models import ViewSetMixin


class ModelViewSet:
    """
    A viewset to allow listing, creating, editing and deleting model instances.
    """

    #: The model for which we are building this viewset
    model: Optional[Type[ViewSetMixin]] = None

    #: The path prefix to use to organize our views.
    url_prefix: Optional[str] = None
    #: The URL namespace to use for our view names.  This should be set to
    #: the ``app_name`` set in the ``urls.py`` where this viewset's patterns
    #: will be added to ``urlpatterns``
    url_namespace: Optional[str] = None
    #: Set this to your :py:class:`wildewidgets.widgets.navigation.BreadcrumbBlock`
    #: class to manage breadcrumbs automatically.
    breadcrumbs_class: Optional[Type[BreadcrumbBlock]] = None
    #: The navbar to use.  We'll highlight our verbose name in any of the
    #: menus within the navbar
    navbar_class: Optional[Type[Navbar]] = None
    #: The template name to use for all views
    template_name: Optional[str] = None

    #: The view class to use for the index view; must be a subclass of
    #: :py:class:`wildewidgets.views.generic.IndexView`.
    index_view_class: Type[IndexView] = IndexView
    #: The :py:class:`wildewidgets.widgets.tables.base.BaseDataTable` subclass
    #: to use for the listing table
    index_table_class: Type[BaseDataTable] = LookupModelTable
    #: A dictionary that we will use as the ``**kwargs`` for the constructor of
    #: :py:attr:`table_class`
    index_table_kwargs: Dict[str, Any] = {
        'striped': True,
        'page_length': 50,
        'buttons': True
    }

    #: The view class to use as the AJAX JSON endpoint for the dataTable; must
    #: be a subclass of :py:class:`wildewidgets.views.generic.TableAJAXView`.
    table_ajax_view_class: Type[View] = TableAJAXView

    #: The view class to use for the index view; must be a subclass of
    #: :py:class:`wildewidgets.views.generic.CreateView`.
    table_bulk_action_view_class: Type[View] = TableBulkActionView

    #: The view class to use for the index view; must be a subclass of
    #: :py:class:`wildewidgets.views.generic.CreateView`.
    create_view_class: Type[View] = CreateView

    #: The view class to use for the index view; must be a subclass of
    #: :py:class:`wildewidgets.views.generic.UpdateView`.
    update_view_class: Type[View] = UpdateView

    #: The view class to use for the index view; must be a subclass of
    #: :py:class:`wildewidgets.views.generic.DeleteView`.
    delete_view_class: Type[View] = DeleteView

    def __init__(
        self,
        model: Type[ViewSetMixin] = None,
        url_prefix: str = None,
        url_namespace: str = None,
        **kwargs
    ):
        #: The model we're describing in this view. It must have
        #: :py:class:`wildewidgets.models.ViewSetMixin` in its class heirarchy
        self.model: Type[ViewSetMixin] = model if model else self.model
        # Tell the model we are its viewset
        self.model.viewset = self
        self.name = slugify(self.model._meta.verbose_name.lower())
        self.url_prefix = url_prefix if url_prefix else self.name
        self.url_namespace = url_namespace

        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_url_name(self, view_name: str, namespace: bool = True) -> str:
        """
        Returns the (possibly) namespaced URL name for the given view.

        Args:
            view_name:
        """
        url_name = f'{self.name}--{view_name}'
        if namespace and self.url_namespace:
            url_name = f'{self.url_namespace}:{url_name}'
        return url_name

    def get_breadcrumbs(self, view_name: str) -> Optional[BreadcrumbBlock]:
        breadcrumbs: Optional[BreadcrumbBlock] = None
        if self.breadcrumbs_class:
            breadcrumbs = self.breadcrumbs_class()  # pylint: disable=not-callable
            if view_name != 'index':
                breadcrumbs.add_breadcrumb(
                    title=self.model.model_verbose_name_plural(),
                    url=reverse_lazy(self.get_url_name('index'))
                )
        return breadcrumbs

    def get_index_table_kwargs(self):
        table_kwargs = deepcopy(self.index_table_kwargs)
        if 'form_actions' not in table_kwargs:
            table_kwargs['form_actions'] = [
                ('delete', 'Delete selected')
            ]
        table_kwargs['ajax_url_name'] = self.get_url_name('table-ajax')
        table_kwargs['form_url'] = reverse_lazy(self.get_url_name('table-bulk-actions'))
        return table_kwargs

    @property
    def index_view(self):
        return self.index_view_class.as_view(
            model=self.model,
            template_name=self.template_name,
            table_class=self.index_table_class,
            table_kwargs=self.get_index_table_kwargs(),
            breadcrumbs=self.get_breadcrumbs('index'),
            navbar_class=self.navbar_class
        )

    @property
    def table_ajax_view(self):
        return self.table_ajax_view_class.as_view(
            model=self.model,
            table_class=self.index_table_class,
            table_kwargs=self.get_index_table_kwargs(),
        )

    @property
    def table_bulk_action_view(self):
        return self.table_bulk_action_view_class.as_view(
            model=self.model,
            url=reverse_lazy(self.get_url_name('index')),
            table_class=self.index_table_class,
            table_kwargs=self.get_index_table_kwargs(),
        )

    @property
    def create_view(self):
        return self.create_view_class.as_view(
            model=self.model,
            template_name=self.template_name,
            breadcrumbs=self.get_breadcrumbs('create'),
            navbar_class=self.navbar_class,
            success_url=reverse_lazy(self.get_url_name('index'))
        )

    @property
    def update_view(self):
        return self.update_view_class.as_view(
            model=self.model,
            template_name=self.template_name,
            breadcrumbs=self.get_breadcrumbs('update'),
            navbar_class=self.navbar_class,
            success_url=reverse_lazy(self.get_url_name('index'))
        )

    @property
    def delete_view(self):
        return self.delete_view_class.as_view(
            model=self.model,
            success_url=reverse_lazy(self.get_url_name('index'))
        )

    def get_urlpatterns(self):
        root = f'{slugify(self.model.model_logger_name())}/'
        if self.url_prefix:
            root = f'{self.url_prefix}/{root}'
        return [
            path(root, self.index_view, name=self.get_url_name('index', namespace=False)),
            path(f"{root}table/ajax/", self.table_ajax_view, name=self.get_url_name('table-ajax', namespace=False)),
            path(
                f"{root}table/bulk/",
                self.table_bulk_action_view,
                name=self.get_url_name('table-bulk-actions', namespace=False)
            ),
            path(f"{root}create/", self.create_view, name=self.get_url_name('create', namespace=False)),
            path(f"{root}<int:pk>/", self.update_view, name=self.get_url_name('update', namespace=False)),
            path(
                f"{root}<int:pk>/delete/",
                self.delete_view,
                name=self.get_url_name('delete', namespace=False)
            )
        ]
