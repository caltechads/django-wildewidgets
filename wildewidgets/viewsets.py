from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any

from django.core.exceptions import ImproperlyConfigured
from django.urls import path, reverse_lazy
from django.utils.text import slugify

from wildewidgets.views.generic import (
    CreateView,
    DeleteView,
    IndexView,
    TableAJAXView,
    TableBulkActionView,
    UpdateView,
)
from wildewidgets.widgets import (
    BaseDataTable,
    BreadcrumbBlock,
    LookupModelTable,
    Navbar,
)

from .models import ViewSetMixin

if TYPE_CHECKING:
    from django.views import View


class ModelViewSet:
    """
    A viewset that provides CRUD operations for a Django model.

    This class simplifies the creation of a complete set of views for a model,
    automatically generating URLs and configuring views for listing, creating,
    updating, and deleting model instances. It follows the Django REST Framework
    ViewSet pattern but for traditional Django views.

    The viewset handles:

    - Index/list view with a data table
    - AJAX endpoint for table data loading
    - Bulk action processing (e.g., bulk delete)
    - Create view with a form
    - Update view with a form
    - Delete view

    To use this class, create a subclass and set at minimum the `model` attribute:

    Example:
        .. code-block:: python

            from wildewidgets import (
                BreadcrumbBlock,
                TablerVerticalNavbar,
                Menu,
                MenuItem,
            )
            from wildewidgets.viewsets import ModelViewSet
            from myapp.models import Book

            class MainMenu(Menu):
                items = [
                    MenuItem(
                        text="Home",
                        icon="house",
                        url=reverse_lazy("core:home"),
                    ),
                    MenuItem(
                        text="Books",
                        icon="mailbox",
                        url=reverse_lazy("core:books--index"),
                    ),
                ]

            class MyNavbar(TablerVerticalNavbar):
                hide_below_viewport: str = "xl"
                branding = Block(
                    LinkedImage(
                        image_src=static("images/logo.png"),
                        image_width="150px",
                        image_alt="MyOrg",
                        css_class="d-flex justify-content-center ms-3",
                        url="https://www.example.com/",
                    ),
                )
                contents = [
                    MainMenu(),
                ]


            class MyBreadcrumbs(BreadcrumbBlock):
                def __init__(self):
                    super().__init__()
                    self.add_breadcrumb(title="Home", url="/")

            class BookViewSet(ModelViewSet):
                model = Book
                url_prefix = "books"
                url_namespace = "myapp"
                breadcrumbs_class = MyBreadcrumbs

            # In urls.py
            urlpatterns += BookViewSet().get_urlpatterns()

    Keyword Args:
        model: The model class to use (must be a
            :py:class:`wildewidgets.ViewSetMixin` subclass)
        url_prefix: Optional prefix for all URLs (defaults to model name)
        url_namespace: Optional namespace for URL names
        **kwargs: Additional attributes to set on the viewset

    Raises:
        ImproperlyConfigured: If model is not provided or not a ViewSetMixin
            subclass, or if model is missing required attributes

    """

    #: The model for which we are building this viewset
    model: type[ViewSetMixin] | None = None

    #: The path prefix to use to organize our views.
    url_prefix: str | None = None
    #: The URL namespace to use for our view names.  This should be set to
    #: the ``app_name`` set in the ``urls.py`` where this viewset's patterns
    #: will be added to ``urlpatterns``
    url_namespace: str | None = None
    #: Set this to your :py:class:`wildewidgets.widgets.navigation.BreadcrumbBlock`
    #: class to manage breadcrumbs automatically.
    breadcrumbs_class: type[BreadcrumbBlock] | None = None
    #: The navbar to use.  We'll highlight our verbose name in any of the
    #: menus within the navbar
    navbar_class: type[Navbar] | None = None
    #: The template name to use for all views
    template_name: str | None = None

    #: The view class to use for the index view; must be a subclass of
    #: :py:class:`wildewidgets.views.generic.IndexView`.
    index_view_class: type[IndexView] = IndexView
    #: The :py:class:`wildewidgets.widgets.tables.base.BaseDataTable` subclass
    #: to use for the listing table
    index_table_class: type[BaseDataTable] = LookupModelTable
    #: A dictionary that we will use as the ``**kwargs`` for the constructor of
    #: :py:attr:`table_class`
    index_table_kwargs: dict[str, Any] = {  # noqa: RUF012
        "striped": True,
        "page_length": 50,
        "buttons": True,
    }

    #: The view class to use as the AJAX JSON endpoint for the dataTable; must
    #: be a subclass of :py:class:`wildewidgets.views.generic.TableAJAXView`.
    table_ajax_view_class: type[View] = TableAJAXView

    #: The view class to use for the index view; must be a subclass of
    #: :py:class:`wildewidgets.views.generic.CreateView`.
    table_bulk_action_view_class: type[View] = TableBulkActionView

    #: The view class to use for the index view; must be a subclass of
    #: :py:class:`wildewidgets.views.generic.CreateView`.
    create_view_class: type[View] = CreateView

    #: The view class to use for the index view; must be a subclass of
    #: :py:class:`wildewidgets.views.generic.UpdateView`.
    update_view_class: type[View] = UpdateView

    #: The view class to use for the index view; must be a subclass of
    #: :py:class:`wildewidgets.views.generic.DeleteView`.
    delete_view_class: type[View] = DeleteView

    def __init__(
        self,
        model: type[ViewSetMixin] | None = None,
        url_prefix: str | None = None,
        url_namespace: str | None = None,
        **kwargs,
    ):
        #: The model we're describing in this view. It must have
        #: :py:class:`wildewidgets.models.ViewSetMixin` in its class heirarchy
        self.model: type[ViewSetMixin] = model if model else self.model
        if not self.model or not issubclass(self.model, ViewSetMixin):
            msg = (
                "model must be either set as a class attribute or passed in as "
                "a kwarg, and it also must be a subclass of ViewSetMixin"
            )
            raise ImproperlyConfigured(msg)
        if not self.model._meta.verbose_name_plural:
            msg = "Model must have a verbose_name_plural set to use breadcrumbs"
            raise ImproperlyConfigured(msg)
        if not self.model._meta.verbose_name:
            msg = "model must have a verbose_name"
            raise ImproperlyConfigured(msg)
        # Tell the model we are its viewset
        self.model.viewset = self
        self.name = slugify(self.model._meta.verbose_name.lower())
        self.url_prefix = url_prefix if url_prefix else self.name
        self.url_namespace = url_namespace

        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_url_name(self, view_name: str, namespace: bool = True) -> str:
        """
        Generate a URL name for a specific view.

        This method creates a URL name by combining the model name with the view name.
        If namespace is True and a URL namespace is set, the namespace is prepended.

        Args:
            view_name: The base name of the view (e.g., "index", "create")
            namespace: Whether to include the namespace prefix if available

        Returns:
            str: The complete URL name for the view

        Example:
            >>> viewset.get_url_name("create")
            'myapp:book--create'  # (if namespace is 'myapp' and model name is 'book')

        """
        url_name = f"{self.name}--{view_name}"
        if namespace and self.url_namespace:
            url_name = f"{self.url_namespace}:{url_name}"
        return url_name

    def get_breadcrumbs(self, view_name: str) -> BreadcrumbBlock | None:
        """
        Create breadcrumb navigation for the specified view.

        This method returns a configured breadcrumb block for the current view.
        For views other than "index", it adds a breadcrumb link back to the index view.

        Args:
            view_name: The name of the view ("index", "create", "update", etc.)

        Returns:
            Configured breadcrumb block, or None if :py:attr:`breadcrumbs_class`
            is not set

        """
        breadcrumbs: BreadcrumbBlock | None = None
        if self.breadcrumbs_class:
            breadcrumbs = self.breadcrumbs_class()  # pylint: disable=not-callable
            if view_name != "index":
                breadcrumbs.add_breadcrumb(
                    title=self.model.model_verbose_name_plural(),  # type: ignore[union-attr]
                    url=reverse_lazy(self.get_url_name("index")),
                )
        return breadcrumbs

    def get_index_table_kwargs(self) -> dict[str, Any]:
        """
        Get keyword arguments for configuring the index table.

        This method creates a dictionary of configuration options for the data table
        on the index page. It automatically sets:
        - Default form actions if none are specified
        - The AJAX URL for fetching data
        - The form URL for bulk actions

        Returns:
            dict[str, Any]: Configuration options for the data table

        """
        table_kwargs = deepcopy(self.index_table_kwargs)
        if "form_actions" not in table_kwargs:
            table_kwargs["form_actions"] = [("delete", "Delete selected")]
        table_kwargs["ajax_url_name"] = self.get_url_name("table-ajax")
        table_kwargs["form_url"] = reverse_lazy(self.get_url_name("table-bulk-actions"))
        return table_kwargs

    @property
    def index_view(self):
        """
        Get the configured index view.

        This property returns a Django view function for listing model instances
        in a data table, with all necessary configuration.

        Returns:
            View callable: Configured index view

        """
        return self.index_view_class.as_view(
            model=self.model,
            template_name=self.template_name,
            table_class=self.index_table_class,
            table_kwargs=self.get_index_table_kwargs(),
            breadcrumbs=self.get_breadcrumbs("index"),
            navbar_class=self.navbar_class,
        )

    @property
    def table_ajax_view(self):
        """
        Get the configured AJAX data endpoint view.

        This property returns a Django view function that serves as the AJAX endpoint
        for the data table, providing data in JSON format.

        Returns:
            View callable: Configured AJAX view

        """
        return self.table_ajax_view_class.as_view(
            model=self.model,
            table_class=self.index_table_class,
            table_kwargs=self.get_index_table_kwargs(),
        )

    @property
    def table_bulk_action_view(self):
        """
        Get the configured bulk action view.

        This property returns a Django view function for processing bulk actions
        on multiple model instances, such as bulk deletion.

        Returns:
            View callable: Configured bulk action view

        """
        return self.table_bulk_action_view_class.as_view(
            model=self.model,
            url=reverse_lazy(self.get_url_name("index")),
            table_class=self.index_table_class,
            table_kwargs=self.get_index_table_kwargs(),
        )

    @property
    def create_view(self):
        """
        Get the configured create view.

        This property returns a Django view function for creating new model instances,
        with form handling and success/error redirects.

        Returns:
            View callable: Configured create view

        """
        return self.create_view_class.as_view(
            model=self.model,
            template_name=self.template_name,
            breadcrumbs=self.get_breadcrumbs("create"),
            navbar_class=self.navbar_class,
            success_url=reverse_lazy(self.get_url_name("index")),
        )

    @property
    def update_view(self):
        """
        Get the configured update view.

        This property returns a Django view function for updating existing model
        instances, with form handling and success/error redirects.

        Returns:
            View callable: Configured update view

        """
        return self.update_view_class.as_view(
            model=self.model,
            template_name=self.template_name,
            breadcrumbs=self.get_breadcrumbs("update"),
            navbar_class=self.navbar_class,
            success_url=reverse_lazy(self.get_url_name("index")),
        )

    @property
    def delete_view(self):
        """
        Get the configured delete view.

        This property returns a Django view function for deleting model instances,
        with success redirect after deletion.

        Returns:
            View callable: Configured delete view

        """
        return self.delete_view_class.as_view(
            model=self.model, success_url=reverse_lazy(self.get_url_name("index"))
        )

    def get_urlpatterns(self):
        """
        Generate URL patterns for all views.

        This method creates a list of URL patterns for all CRUD operations:
        - Index/list view
        - AJAX endpoint for table data
        - Bulk action processing
        - Create view
        - Update view
        - Delete view

        The URLs follow a consistent pattern based on the model name and any prefix.

        Returns:
            list: Django URL patterns for all views

        Example:
            >>> urlpatterns = BookViewSet().get_urlpatterns()
            >>> # URLs will include patterns like 'books/', 'books/create/', etc.

        """
        root = f"{slugify(self.model.model_logger_name())}/"
        if self.url_prefix:
            root = f"{self.url_prefix}/{root}"
        return [
            path(
                root, self.index_view, name=self.get_url_name("index", namespace=False)
            ),
            path(
                f"{root}table/ajax/",
                self.table_ajax_view,
                name=self.get_url_name("table-ajax", namespace=False),
            ),
            path(
                f"{root}table/bulk/",
                self.table_bulk_action_view,
                name=self.get_url_name("table-bulk-actions", namespace=False),
            ),
            path(
                f"{root}create/",
                self.create_view,
                name=self.get_url_name("create", namespace=False),
            ),
            path(
                f"{root}<int:pk>/",
                self.update_view,
                name=self.get_url_name("update", namespace=False),
            ),
            path(
                f"{root}<int:pk>/delete/",
                self.delete_view,
                name=self.get_url_name("delete", namespace=False),
            ),
        ]
