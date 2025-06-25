from __future__ import annotations

import logging
from copy import deepcopy
from typing import TYPE_CHECKING, Any, cast

from braces.views import (
    FormInvalidMessageMixin,
    FormValidMessageMixin,
    LoginRequiredMixin,
    MessageMixin,
)
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import redirect
from django.views.generic import CreateView as DjangoCreateView
from django.views.generic import TemplateView, View
from django.views.generic import UpdateView as DjangoUpdateView
from django.views.generic.edit import (
    BaseDeleteView,
    BaseUpdateView,
)

from ..forms import AbstractRelatedFieldForm, ToggleableManyToManyFieldForm
from ..models import (
    ViewSetMixin,
    model_logger_name,
    model_name,
    model_verbose_name,
    model_verbose_name_plural,
)
from ..views import TableActionFormView, WidgetInitKwargsMixin
from ..widgets import (
    BaseDataTable,
    Block,
    BreadcrumbBlock,
    CardWidget,
    CrispyFormWidget,
    LookupModelTable,
    NavbarMixin,
    RowDeleteButton,
    RowEditButton,
    TwoColumnLayout,
    Widget,
    WidgetListLayoutHeader,
)
from .mixins import StandardWidgetMixin
from .permission import PermissionRequiredMixin

if TYPE_CHECKING:
    from django.forms import BaseModelForm, Form, ModelForm
    from django.http import HttpRequest, HttpResponse, HttpResponseBase, QueryDict

    from ..widgets.tables import RowActionButton

logger = logging.getLogger(__name__)


# --------------------------------------------
# Abastract Widgets
# --------------------------------------------


class AbstractFormPageLayout(Block):
    """
    An abstract class for making whole page layouts for a form page.

    This class provides a structured layout for form pages (create/update pages),
    with a title, optional subtitle, and form content area. It automatically handles
    the setup of these elements and provides an extensible framework for customized
    form layouts.

    The layout will automatically infer appropriate titles and subtitles based on
    the view context, but these can be overridden when needed.

    Note:
        Subclasses must override the :py:meth`get_form` method to provide the
        actual form rendering implementation.

    Example:
        .. code-block:: python

            from wildewidgets import (
                AbstractFormPageLayout,
                TwoColumnLayout,
                CrispyFormWidget,
            )

            class HelpTextWidget(Block):
                def __init__(self, **kwargs):
                    super().__init__(**kwargs)
                    self.add_block(
                        Block(
                            "This is some help text for the form.",
                            name="help-text",
                            css_class="text-muted",
                        )
                    )

            class MyFormLayout(AbstractFormPageLayout):
                def get_form(self):
                    layout = TwoColumnLayout()
                    layout.add_to_left(CrispyFormWidget(form=self.view.get_form()))
                    layout.add_to_right(HelpTextWidget())
                    return layout

    """

    block: str = "form-layout"

    #: Use this as our page ittle
    title: str | None = None
    #: Use this as our page subtitle.  This will appear directly below
    #: the page title.  Typically set this to a string naming the object
    #: we're updating
    subtitle: str | None = None

    def __init__(
        self,
        view: GenericViewMixin,
        title: str | None = None,
        subtitle: str | None = None,
        **kwargs,
    ):
        self.view = view
        self.title = title if title else self.title
        self.subtitle = subtitle if subtitle else self.subtitle
        if not self.title:
            if isinstance(self.view, DjangoCreateView):
                self.title = f"Create {self.view.model_verbose_name}"
            elif isinstance(self.view, DjangoUpdateView):
                self.title = f"Update {self.view.model_verbose_name}"
            else:
                self.title = f"Manage {self.view.model_verbose_name}"
        if not self.subtitle and view.object is not None:
            self.subtitle = str(view.object)
        super().__init__(**kwargs)
        self.add_block(self.get_title())
        if self.subtitle:
            self.add_block(self.get_subtitle())
        self.add_block(self.get_form())

    def get_title(self) -> Block:
        """
        Create a title block for the form layout.

        Returns:
            Block: A Block widget containing the page title with appropriate styling

        Raises:
            AssertionError: If title is not set

        """
        assert self.title, "You must set a title for your form layout"  # noqa: S101
        title = Block(
            self.title,
            name=f"{self.block}__title",
            tag="h1",
        )
        if not self.subtitle:
            title.add_class("mb-5")
        return title

    def get_subtitle(self) -> Block:
        """
        Create a subtitle block for the form layout.

        Returns:
            Block: A Block widget containing the page subtitle with appropriate styling

        Raises:
            AssertionError: If subtitle is not set

        """
        assert self.subtitle, "You must set a subtitle for your form layout"  # noqa: S101
        return Block(
            self.subtitle,
            name=f"{self.block}__subtitle",
            css_class="text-muted fs-6 text-uppercase mb-5",
        )

    def get_form(self) -> Block:
        """
        Create the main form content for the layout.

        This method must be overridden by subclasses to provide the specific form
        rendering implementation.

        Returns:
            Block: A Block widget containing the form content

        Raises:
            NotImplementedError: Always, as this is an abstract method

        """
        raise NotImplementedError


# --------------------------------------------
# Widgets
# --------------------------------------------


class IndexTableWidget(Block):
    """
    A widget for displaying a model listing table with a header.

    This block renders a table for displaying model instances with a header that
    includes the model's plural name, a count badge, and optionally a create button.
    It's primarily used in list views to provide a consistent interface for
    viewing and managing model collections.

    Attributes:
        model: The Django model class being displayed
        show_create_button: Whether to show a "New" button that links to the create view

    Example:
        .. code-block:: python

            from django.db.models import Model
            from wildewidgets import IndexTableWidget, BasicModelTable, ViewSetMixin

            class Book(Model, ViewSetMixin):
                title = models.CharField(max_length=255)
                author = models.CharField(max_length=255)
                published_date = models.DateField()

                class Meta:
                    verbose_name = "book"
                    verbose_name_plural = "books"


            class BookTable(BasicModelTable):
                model = Book
                fields = ["title", "author", "published_date"]


            widget = IndexTableWidget(
                model=Book,
                table=BookTable(),
                show_create_button=True
            )

    Args:
        model: The model class being displayed in the table
        table: The data table instance to display
        show_create_button: Whether to show a button to create new instances

    Keyword Args:
        **kwargs: Additional arguments passed to the parent Block

    """

    def __init__(
        self,
        model: type[ViewSetMixin],
        table: BaseDataTable,
        show_create_button: bool = True,
        **kwargs,
    ):
        self.model = model
        self.show_create_button = show_create_button
        super().__init__(**kwargs)
        self.add_block(self.get_title())
        self.add_block(CardWidget(widget=table))

    def get_title(self) -> WidgetListLayoutHeader:
        """
        Create a header widget for the table.

        This creates a header with the model's verbose_name_plural, a badge showing
        the count of records, and optionally a "New" button for creating instances.

        Returns:
            WidgetListLayoutHeader: The header widget

        Raises:
            ImproperlyConfigured: If the model doesn't have verbose_name or
                verbose_name_plural

        """
        if not self.model._meta.verbose_name_plural:
            msg = (
                "This model has no verbose_name_plural set, so we can't display a "
                "title."
            )
            raise ImproperlyConfigured(msg)
        if not self.model._meta.verbose_name:
            msg = "This model has no verbose_name set, so we can't display a title."
            raise ImproperlyConfigured(msg)
        header = WidgetListLayoutHeader(
            header_text=self.model._meta.verbose_name_plural.capitalize(),
            badge_text=self.model.objects.count(),
        )
        if self.show_create_button:
            header.add_link_button(
                text=f"New {self.model._meta.verbose_name.capitalize()}",
                color="primary",
                url=self.model.get_create_url(),
            )
        return header


class FormPageLayout(AbstractFormPageLayout):
    """
    A standard two-column layout for form pages.

    This class implements a common layout pattern for form pages with a
    two-column structure. The form is placed in the left column (which takes
    9/12 of the width by default) and leaves space for additional content in the
    right column if needed.

    Attributes:
        left_column_width: Width of the left column (1-12 in Bootstrap grid
            system)

    Example:
        .. code-block:: python

            from django.views.generic.edit import CreateView
            from wildewidgets import FormPageLayout

            class MyFormView(CreateView):
                layout_widget = FormPageLayout
                # The form will be rendered in a two-column layout

    """

    left_column_width: int = 9

    def get_form(self) -> Block:
        """
        Create a two-column layout with the form in the left column.

        The form is rendered with a crispy form widget and given a shadow and white
        background for visual distinction.

        Returns:
            Block: A TwoColumnLayout containing the form

        """
        layout = TwoColumnLayout(left_column_width=9)
        form_widget = CrispyFormWidget(
            form=self.view.get_form(), css_class="shadow bg-white p-4"
        )
        layout.add_to_left(form_widget)
        return layout


# --------------------------------------------
# View mixins
# --------------------------------------------


class GenericViewMixin:
    """
    Mixin providing common functionality for views that work with models.

    This mixin adds methods and properties that simplify working with models in
    views, including logging utilities, permission handling, and UI helpers like
    breadcrumbs.  It's designed to be used with Django class-based views and is
    a core component of the generic views system.

    Example:
        .. code-block:: python

            from django.views.generic import TemplateView
            from wildewidgets.views.generic import GenericViewMixin

            from myapp.models import MyModel

            class MyView(GenericViewMixin, TemplateView):
                model = MyModel
                required_model_permissions = ['view']

                def get_content(self):
                    # Use self.model_verbose_name, self.logging_extra, etc.

    """

    #: Set this to the model permissions the user must have in order
    #: to be authorized for this view:
    required_model_permissions: list[str] = []  # noqa: RUF012
    #: Set this to the logger of your choice
    logger: Any = logger
    #: Set this to your :py:class:`wildewidgets.widgets.navigation.BreadcrumbBlock`
    #: to manage breadcrumbs automatically.
    breadcrumbs: BreadcrumbBlock | None = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.breadcrumbs is not None:
            self.breadcrumbs = deepcopy(self.breadcrumbs)

    @property
    def model_name(self) -> str:
        """
        Get the name of the model class.

        Returns:
            str: The model class name

        """
        if hasattr(self.model, "model_name"):
            return self.model.model_name()
        return model_name(self.model)

    @property
    def model_logger_name(self) -> str:
        """
        Get a suitable name for logging messages about this model.

        Returns:
            str: The model name in lowercase, suitable for logging

        """
        if hasattr(self.model, "model_logger_name"):
            return self.model.model_logger_name()
        return model_logger_name(self.model)

    @property
    def model_verbose_name(self) -> str:
        """
        Get the verbose name of the model, properly capitalized.

        Returns:
            str: The model's verbose name

        """
        if hasattr(self.model, "model_verbose_name"):
            return self.model.model_verbose_name()
        return model_verbose_name(self.model)

    @property
    def model_verbose_name_plural(self) -> str:
        """
        Get the plural verbose name of the model, properly capitalized.

        Returns:
            str: The model's plural verbose name

        """
        if hasattr(self.model, "model_verbose_name_plural"):
            return self.model.model_verbose_name_plural()
        return model_verbose_name_plural(self.model)

    def get_client_ip(self) -> str:
        """
        Get the IP address of the client making the request.

        This method checks for ``X-Forwarded-For`` headers first (for clients
        behind proxies) and falls back to ``REMOTE_ADDR`` if needed.

        Returns:
            str: The client's IP address

        """
        x_forwarded_for = self.request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return self.request.META.get("REMOTE_ADDR")

    @property
    def logging_extra(self) -> str:
        """
        Get extra contextual information for log messages.

        This property builds a string containing:

        - The client's IP address
        - The current user's username
        - The primary key of the current object (if applicable)

        Returns:
            str: A space-separated string of key=value pairs

        """
        data = {}
        data["remote_ip"] = self.get_client_ip()
        data["username"] = self.request.user.username
        if hasattr(self, "object"):
            data["pk"] = self.object.pk
        return " ".join([f"{key}={value}" for key, value in data.items()])

    def get_menu_item(self) -> str | None:
        """
        Get the name of the main menu item that should be set as active.

        Returns:
            str | None: The plural verbose name of the model

        """
        return self.model_verbose_name_plural

    def get_permissions_required(self) -> list[str]:
        """
        Get the list of permissions required to access this view.

        This method combines permissions from the parent class with
        model-specific permissions based on the required_model_permissions
        attribute.

        Returns:
            list[str]: List of permission strings

        """
        required_perms = set(super().get_permissions_required())  # type: ignore[misc]
        required_perms.update(
            self.get_model_permissions(self.model, self.required_model_permissions)
        )
        return list(required_perms)

    def get_breadcrumbs(self) -> BreadcrumbBlock | None:
        """
        Get the breadcrumbs for this view, adding the current page title.

        Returns:
            BreadcrumbBlock | None: The updated breadcrumb block or None

        """
        if self.breadcrumbs:
            self.breadcrumbs.add_breadcrumb(title=self.get_title())
        return self.breadcrumbs


class GenericDatatableMixin:
    """
    Mixin providing datatable functionality for views that display model tables.

    This mixin provides methods for configuring and instantiating DataTable
    widgets with appropriate settings and row actions. It handles common tasks
    like setting up action buttons based on user permissions and configuring
    table options.

    Example:
        .. code-block:: python

            from django.views.generic import TemplateView
            from wildewidgets import GenericDatatableMixin

            from myapp.models import MyModel
            from myapp.wildewidgets import MyCustomTable

            class MyListView(GenericDatatableMixin, TemplateView):
                model = MyModel
                table_class = MyCustomTable

                def get_content(self):
                    return self.get_table()

    """

    model: type[ViewSetMixin] | None

    #: The :py:class:`wildewidgets.widgets.tables.base.BaseDataTable` subclass
    #: to use for the listing table
    table_class: type[BaseDataTable] = LookupModelTable
    #: A dictionary that we will use as the ``**kwargs`` for the constructor of
    #: :py:attr:`table_class`
    table_kwargs: dict[str, Any] = {  # noqa: RUF012
        "striped": True,
        "page_length": 25,
        "buttons": True,
    }

    def get_table_kwargs(self) -> dict[str, Any]:
        """
        Get keyword arguments for table initialization.

        This method builds a dictionary of options to pass to the table constructor.
        If bulk actions are enabled but no specific actions are defined, it adds
        a default "delete" action.

        Returns:
            dict[str, Any]: Keyword arguments for the table constructor

        """
        table_kwargs = self.table_kwargs
        if "form_actions" not in table_kwargs and self.bulk_action_url_name:
            table_kwargs["form_actions"] = [
                ("delete", f"Delete {self.model_verbose_name}")
            ]

        return table_kwargs

    def get_table(self, *args, **kwargs) -> BaseDataTable:
        """
        Create and configure a datatable instance.

        This method instantiates the table_class with appropriate options and
        row action buttons based on user permissions.

        Args:
            *args: Positional arguments passed to the table constructor

        Keyword Args:
            **kwargs: Keyword arguments passed to the table constructor

        Returns:
            BaseDataTable: The configured datatable instance

        """
        kwargs.update(self.get_table_kwargs())
        kwargs["model"] = self.model
        actions: list[RowActionButton] = []
        if self.user_can_update():
            actions.append(RowEditButton())
        if self.user_can_delete():
            actions.append(RowDeleteButton())
        if actions:
            kwargs["actions"] = actions
        return self.table_class(*args, **kwargs)


# --------------------------------------------
# Views
# --------------------------------------------


class IndexView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    GenericViewMixin,
    GenericDatatableMixin,
    NavbarMixin,
    StandardWidgetMixin,
    TemplateView,
):
    """
    Generic view for displaying a list of model instances in a table.

    This view provides a complete implementation for displaying model data in a
    table with support for sorting, filtering, pagination, and row actions. It
    requires minimal configuration - typically just setting the model attribute.

    The view automatically handles:

    - User authentication and permission checking
    - Table configuration and rendering
    - Create button based on user permissions

    Attributes:
        model: The model class to display
        required_model_permissions: List of permissions required to access this view

    Example:
        .. code-block:: python

            from django.db import models
            from wildewidgets import IndexView

            class Book(models.Model, ViewSetMixin):
                title = models.CharField(max_length=255)
                author = models.CharField(max_length=255)
                published_date = models.DateField()

                class Meta:
                    verbose_name = "book"
                    verbose_name_plural = "books"

            class BookListView(IndexView):
                model = Book
                # That's it! The view is ready to use.

    """

    #: The model we're describing in this view. It must have
    #: :py:class:`wildewidgets.models.ViewSetMixin` in its class heirarchy
    model: type[ViewSetMixin] | None = None

    required_model_permissions: list[str] = [  # noqa: RUF012
        "view",
        "add",
        "change",
        "delete",
    ]

    def get_title(self) -> str:
        """
        Get the page title for this view.

        Returns:
            str: The plural verbose name of the model

        """
        return self.model_verbose_name_plural

    def get_content(self) -> Widget:
        """
        Get the main content for this view.

        Returns:
            Widget: An IndexTableWidget configured for the model

        Raises:
            ImproperlyConfigured: If model is not set

        """
        if not self.model:
            msg = "You must set the model attribute on this view to use it."
            raise ImproperlyConfigured(msg)
        return IndexTableWidget(
            self.model, self.get_table(), show_create_button=self.user_can_create()
        )


class TableAJAXView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    WidgetInitKwargsMixin,
    GenericDatatableMixin,
    View,
):
    """
    View that handles AJAX requests for datatable data.

    This view processes AJAX requests from the client-side DataTables library,
    returning filtered, sorted, and paginated data as JSON. It handles all the
    server-side processing required by DataTables.

    This view is typically used on its own, without a template, to provide
    data source for the model.

    By default we use :py:class:`wildewidgets.LookupModelTable` as the
    :py:attr:`table_class`, but you can override this to use any
    :py:class:`wildewidgets.widgets.tables.base.BaseDataTable` subclass.

    Example:

        .. code-block:: python

            from wildewidgets.views.generic import TableAJAXView

            from myapp.models import MyModel

            class MyModelTableAJAXView(TableAJAXView):
                model = MyModel


    """

    #: The model we're describing in this view. It must have
    #: :py:class:`wildewidgets.models.ViewSetMixin` in its class heirarchy
    model: type[ViewSetMixin] | None = None

    required_model_permissions: list[str] = ["view", "add", "change", "delete"]  # noqa: RUF012

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponseBase:
        """
        Process incoming requests and delegate to the table's dispatch method.

        This method extracts CSRF token and initialization parameters from the
        request, sets them on the table instance, and then delegates to the
        table's own dispatch method for handling the AJAX request.

        Args:
            request: The HTTP request
            *args: Additional positional arguments

        Kwargs:
            **kwargs: Additional keyword arguments

        Returns:
            HttpResponse: The JSON response from the table

        """
        csrf_token = request.GET.get("csrf_token", "")
        extra_data = self.get_decoded_extra_data(request)
        initargs = extra_data.get("args", [])
        initkwargs = extra_data.get("kwargs", {})
        table = self.get_table(*initargs, **initkwargs)
        table.request = request
        table.csrf_token = csrf_token
        table.args = initargs
        table.kwargs = initkwargs
        return table.dispatch(request, *args, **kwargs)


class TableBulkActionView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    GenericViewMixin,
    GenericDatatableMixin,
    MessageMixin,
    TableActionFormView,
):
    """
    View that handles bulk actions on multiple table rows.

    This view processes form submissions for bulk actions on datatable rows,
    such as deleting multiple items at once. It provides a default implementation
    for bulk deletion and can be extended for other bulk actions.

    Example:
        .. code-block:: python

            from wildewidgets import TableBulkActionView

            class BookBulkActionView(TableBulkActionView):
                model = Book

                def process_archive_action(self, items):
                    # Custom bulk action implementation
                    Book.objects.filter(id__in=items).update(archived=True)

    """

    #: The model we're describing in this view. It must have
    #: :py:class:`wildewidgets.models.ViewSetMixin` in its class heirarchy
    model: type[ViewSetMixin] | None = None

    #: Set this to the logger of your choice
    logger: Any = logger

    required_model_permissions: list[str] = ["delete"]  # noqa: RUF012

    def process_delete_action(self, items: list[str]) -> None:
        """
        Process a bulk delete action.

        This method deletes all model instances with IDs in the provided list,
        logs the action, and displays a success message.

        Args:
            items: List of primary key strings for the items to delete

        """
        qs = self.model.objects.filter(id__in=items)  # type: ignore[union-attr]
        count = qs.count()
        qs.delete()
        self.logger.info(
            "%s.bulk.delete ids=%s %s",
            self.model_logger_name,
            ",".join(items),
            self.logging_extra,
        )
        self.messages.success(
            f"Deleted {count} {self.model.model_verbose_name_plural()}."  # type: ignore[union-attr]
        )


class CreateView(  # type: ignore[misc]
    LoginRequiredMixin,
    PermissionRequiredMixin,
    FormInvalidMessageMixin,
    FormValidMessageMixin,
    GenericViewMixin,
    NavbarMixin,
    StandardWidgetMixin,
    DjangoCreateView,
):
    """
    Generic view for creating new model instances.

    This view provides a complete implementation for creating new model instances
    with form validation, permission checking, and success/error messaging. It
    uses the :py:class:`wildewidgets.FormPageLayout` by default to render the form in an
    attractive layout.

    Example:
        .. code-block:: python

            from django.db import models
            from wildewidgets import CreateView, ViewSetMixin

            class Book(models.Model, ViewSetMixin):
                title = models.CharField(max_length=255)
                author = models.CharField(max_length=255)
                published_date = models.DateField()

                class Meta:
                    verbose_name = "book"
                    verbose_name_plural = "books"

            class BookCreateView(CreateView):
                model = Book
                fields = ['title', 'author', 'published_date']

    """

    required_model_permissions: list[str] = ["add"]  # noqa: RUF012

    #: Use this :py:class:`AbstractFormPageLayout` subclass to render our page
    layout_widget: type[AbstractFormPageLayout] = FormPageLayout

    def get_form_invalid_message(self):
        """
        Get the message to display when form validation fails.

        This method also logs the validation failure.

        Returns:
            str: The error message

        """
        self.logger.warning(
            "%s.create.failed.validation %s", self.model_logger_name, self.logging.extra
        )
        return (
            f"Couldn't create this {self.model_verbose_name} due to validation errors; "
            "see below."
        )

    def get_form_valid_message(self):
        """
        Get the message to display when a new instance is successfully created.

        This method also logs the successful creation.

        Returns:
            str: The success message

        """
        self.logger.info(
            "%s.create.success %s", self.model_logger_name, self.logging_extra
        )
        return f'Created {self.model_verbose_name} "{self.object!s}"!'

    def get_form_class(self) -> type[Form | ModelForm] | None:  # type: ignore[override]
        """
        Get the form class to use for creating the model instance.

        If the model has a get_create_form_class method, use that form class.
        Otherwise, fall back to the default behavior.

        Returns:
            type: The form class to use

        """
        if hasattr(self.model, "get_create_form_class"):
            return cast("type[ViewSetMixin]", self.model).get_create_form_class()
        return super().get_form_class()

    def get_title(self) -> str:
        """
        Get the page title for this view.

        Returns:
            str: A title indicating creation of a new instance

        """
        return f"Create {self.model_verbose_name}"

    def get_content(self) -> Widget:
        """
        Get the main content for this view.

        Returns:
            Widget: A form layout widget with the create form

        """
        return self.layout_widget(self, modifier="create")


class UpdateView(  # type: ignore[misc]
    LoginRequiredMixin,
    PermissionRequiredMixin,
    FormInvalidMessageMixin,
    FormValidMessageMixin,
    GenericViewMixin,
    NavbarMixin,
    StandardWidgetMixin,
    DjangoUpdateView,
):
    """
    Generic view for updating existing model instances.

    This view provides a complete implementation for updating model instances
    with form validation, permission checking, and success/error messaging. It
    uses the FormPageLayout by default to render the form in an attractive layout.

    Example:
        .. code-block:: python

            from django.db import models
            from wildewidgets import CreateView, ViewSetMixin

            class Book(models.Model, ViewSetMixin):
                title = models.CharField(max_length=255)
                author = models.CharField(max_length=255)
                published_date = models.DateField()

                class Meta:
                    verbose_name = "book"
                    verbose_name_plural = "books"

            class BookUpdateView(UpdateView):
                model = Book
                fields = ['title', 'author', 'published_date']

    """

    required_model_permissions: list[str] = ["change"]  # noqa: RUF012

    #: Use this :py:class:`AbstractFormPageLayout` subclass to render our page
    layout_widget: type[AbstractFormPageLayout] = FormPageLayout

    def get_form_invalid_message(self):
        """
        Get the message to display when form validation fails.

        This method also logs the validation failure.

        Returns:
            str: The error message

        """
        self.logger.warning(
            "%s.update.failed.validation %s", self.model_logger_name, self.logging.extra
        )
        return (
            f"Couldn't update this {self.model_verbose_name} due to validation errors; "
            "see below."
        )

    def get_form_valid_message(self):
        """
        Get the message to display when an instance is successfully updated.

        This method also logs the successful update.

        Returns:
            str: The success message

        """
        self.logger.info(
            "%s.update.success %s", self.model_logger_name, self.logging_extra
        )
        return f'Updated {self.model_verbose_name} "{self.object!s}"!'

    def get_form_class(self) -> type[BaseModelForm]:
        """
        Get the form class to use for updating the model instance.

        If the object has a get_update_form_class method, use that form class.
        Otherwise, fall back to the default behavior.

        Returns:
            type: The form class to use

        """
        if hasattr(self.object, "get_update_form_class"):
            return self.object.get_update_form_class()
        return super().get_form_class()

    def get_title(self) -> str:
        """
        Get the page title for this view.

        Returns:
            str: A title indicating update of the instance

        """
        return f'Update {self.model_verbose_name} "{self.object!s}"'

    def get_content(self) -> Widget:
        """
        Get the main content for this view.

        Returns:
            Widget: A form layout widget with the update form

        """
        return self.layout_widget(self, modifier="update")


class DeleteView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    GenericViewMixin,
    FormInvalidMessageMixin,
    FormValidMessageMixin,
    BaseDeleteView,
):
    """
    Generic view for deleting model instances.

    This view provides a complete implementation for deleting model instances
    with permission checking and success/error messaging. It only responds to
    POST requests for security reasons.

    Example:
        .. code-block:: python

            from django.db import models
            from wildewidgets import DeleteView, ViewSetMixin

            class Book(models.Model, ViewSetMixin):
                title = models.CharField(max_length=255)
                author = models.CharField(max_length=255)
                published_date = models.DateField()

                class Meta:
                    verbose_name = "book"
                    verbose_name_plural = "books"


            class BookDeleteView(DeleteView):
                model = Book
                success_url = reverse_lazy('book-list')

    """

    #: The model we're describing in this view. It must have
    #: :py:class:`wildewidgets.models.ViewSetMixin` in its class heirarchy
    model: type[ViewSetMixin] | None = None  # type: ignore[assignment]

    #: The HTTP methods this view responds to. We only allow POST for security.
    http_method_names: list[str] = ["post"]  # noqa: RUF012

    #: The required model permissions for this view.
    required_model_permissions: list[str] = ["delete"]  # noqa: RUF012

    def get_form_invalid_message(self):
        """
        Get the message to display when deletion fails.

        This method also logs the failure.

        Returns:
            str: The error message

        """
        self.logger.warning("%s.delete.failed.validation", self.model_logger_name)
        return f'Couldn\'t delete {self.model_verbose_name} "{self.object!s}"'

    def get_form_valid_message(self):
        """
        Get the message to display when an instance is successfully deleted.

        This method also logs the successful deletion.

        Returns:
            str: The success message

        """
        self.logger.info(
            "%s.delete.success %s", self.model_logger_name, self.logging_extra
        )
        return f'Deleted {self.model_verbose_name} "{self.object!s}"!'

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:  # noqa: ARG002
        """
        Handle form validation failures by redirecting to the success URL.

        Since DeleteView often doesn't render a form, we redirect even on validation
        failures rather than re-rendering the form.

        Args:
            form: The form that failed validation (unused)

        Returns:
            HttpResponse: Redirect to success_url

        """
        return redirect(self.get_success_url())

    def get_form_class(self) -> type[BaseModelForm]:
        """
        Get the form class to use for deleting the model instance.

        If the object has a get_delete_form_class method, use that form class.
        Otherwise, fall back to the default behavior.

        Returns:
            type: The form class to use

        """
        if hasattr(self.object, "get_delete_form_class"):
            return self.object.get_delete_form_class()
        return super().get_form_class()


class ManyToManyRelatedFieldView(  # type: ignore[misc]
    LoginRequiredMixin,
    PermissionRequiredMixin,
    FormValidMessageMixin,
    MessageMixin,
    GenericViewMixin,
    BaseUpdateView,
):
    """
    View for managing many-to-many relationships on a model.

    This view provides a specialized interface for editing many-to-many relationships
    on a model instance. It uses the ToggleableManyToManyFieldForm by default,
    which provides a user-friendly interface for adding and removing related objects.

    Example:
        .. code-block:: python

            from django.db import models
            from wildewidgets import ManyToManyRelatedFieldView, ViewSetMixin

            class Book(models.Model, ViewSetMixin):
                title = models.CharField(max_length=255)
                author = models.CharField(max_length=255)
                published_date = models.DateField()

                class Meta:
                    verbose_name = "book"
                    verbose_name_plural = "books"

            class BookAuthorsView(ManyToManyRelatedFieldView):
                model = Book
                field_name = 'authors'

    """

    #: The name of the many-to-many field to edit
    field_name: str | None = None
    #: The form class to use for editing the relationship
    form_class: type[AbstractRelatedFieldForm] = ToggleableManyToManyFieldForm

    #: The required model permissions for this view.
    required_model_permissions: list[str] = ["change"]  # noqa: RUF012

    @property
    def model_logger_name(self) -> str:
        """
        Get a suitable name for logging messages about this field.

        Returns:
            str: The model logger name with the field name appended

        """
        return f"{super().model_logger_name}.{self.field_name}"

    @property
    def field_verbose_name(self) -> str:
        """
        Get the verbose name of the field being edited.

        Returns:
            str: The field's verbose name, capitalized

        Raises:
            AssertionError: If field_name is not set

        """
        assert self.field_name, "You must set field_name on this view"  # noqa: S101
        return self.model._meta.get_field(self.field_name).verbose_name.capitalize()  # type: ignore[union-attr]

    def get_form_kwargs(self) -> dict[str, Any]:
        """
        Get keyword arguments for form initialization.

        This method adds the field_name to the form kwargs.

        Returns:
            dict: Keyword arguments for the form constructor

        """
        kwargs = super().get_form_kwargs()
        kwargs["field_name"] = self.field_name
        return kwargs

    def form_invalid(self, form: Form) -> HttpResponse:
        """
        Handle form validation failures.

        This method logs the validation failure, adds error messages for each
        validation error, and redirects to the success URL.

        Args:
            form: The form that failed validation

        Returns:
            HttpResponse: Redirect to success_url

        """
        self.logger.warning(
            "%s.update.failed.validation %s", self.model_logger_name, self.logging.extra
        )
        self.messages.error(
            f"Couldn't update {self.field_verbose_name} on {self.model_verbose_name} "
            f'"{self.object!s}"'
        )
        for k, errors in form.errors.as_data().items():
            for error in errors:
                self.messages.error(f"{k}: {error.message}")
        return redirect(self.get_success_url())

    def get_form_valid_message(self):
        """
        Get the message to display when the relationship is successfully updated.

        This method also logs the successful update.

        Returns:
            str: The success message

        """
        self.logger.info(
            "%s.update.success %s", self.model_logger_name, self.logging_extra
        )
        return (
            f"Updated {self.field_verbose_name} on {self.model_verbose_name} "
            f'"{self.object!s}"!'
        )

    def get_success_url(self) -> str:
        """
        Get the URL to redirect to after successful form submission.

        If no explicit success_url is set, try to get the update URL or absolute URL
        of the object.

        Returns:
            str: The URL to redirect to

        """
        success_url = super().get_success_url()
        if not success_url:
            if hasattr(object, "get_update_url"):
                return self.object.get_update_url()
            return self.object.get_absolute_url()
        return success_url


class HTMXView(TemplateView):
    """
    View for rendering a single widget in response to HTMX requests.

    This view is designed to work with HTMX (https://htmx.org/) for partial page
    updates. It renders a single widget with the request parameters passed as
    constructor arguments to the widget.

    Example:
        The python code:

        .. code-block:: python

            from django.db import models
            from wildewidgets import ManyToManyRelatedFieldView, Block

            class UserProfileWidget(Block):
                title: str = "User Profile"
                icon: str = "user"

                def __init__(self, *blocks, **kwargs):
                    super().__init__(**kwargs)
                    self.add_block("This is the user profile widget")


            class UserProfileHTMXView(HTMXView):
                widget_class = UserProfileWidget

        In your template, you can use HTMX to load this view:

        .. code-block:: html

            <div hx-get="/book/123/" hx-trigger="click">Load book</div>


        If you want to include the request object in the widget kwargs, set
        `include_request` to `True`:

        .. code-block:: python

            class UserProfileWidget(Block):
                title: str = "User Profile"
                icon: str = "user"

                def __init__(
                    self,
                    *blocks,
                    request: HttpRequest | None = None,
                    **kwargs
                ):
                    self.request = request
                    # Do something with the request if needed
                    super().__init__(**kwargs)
                    self.add_block("This is the user profile widget")


            class UserProfileHTMXView(HTMXView):
                widget_class = UserProfileWidget
                include_request = True

    Keyword Args:
        **kwargs: Additional keyword arguments to pass to the
            :py:class:`django.views.generic.base.TemplateView`

    """

    #: The Django template to use for rendering the widget
    template_name: str = "wildewidgets/htmx_base.html"
    #: The widget class to instantiate and render
    widget_class: type[Block | Widget] | None = None
    #: Whether to include the request object in the widget kwargs, and
    #: in the context data passed to the template.
    include_request: bool = False

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.data: dict[str, Any] = {}

    def get_content(self, **kwargs) -> Widget:  # noqa: ARG002
        """
        Get the widget instance to render.

        This method instantiates the widget_class with the request parameters.

        Keyword Args:
            **kwargs: Additional arguments (unused)

        Returns:
            Widget: The instantiated widget

        Raises:
            ImproperlyConfigured: If widget_class is not set

        """
        if self.widget_class:
            if self.include_request:
                self.data["request"] = self.request
            return self.widget_class(**self.data)
        msg = "You must set widget_class on this view"
        raise ImproperlyConfigured(msg)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """
        Get the context data for rendering the template.

        This method adds the widget instance to the template context.

        Args:
            **kwargs: Additional context data

        Returns:
            dict: The template context

        """
        context = super().get_context_data(**kwargs)
        context["content"] = self.get_content(**self.data)
        return context

    def set_data(self, request_data: QueryDict) -> None:
        """
        Extract and process data from the request.

        This method converts the request QueryDict to a regular dictionary and
        removes the 'submit' key if present.

        Args:
            request_data: The request.GET or request.POST data

        """
        self.data = request_data.dict()
        if "submit" in self.data:
            del self.data["submit"]

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        Handle GET requests.

        This method extracts data from the GET parameters and renders the template.

        Args:
            request: The HTTP request
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            HttpResponse: The rendered template

        """
        self.set_data(request.GET)
        return super().get(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        Handle POST requests.

        This method extracts data from the POST parameters and renders the template.

        Args:
            request: The HTTP request
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            HttpResponse: The rendered template

        """
        self.set_data(request.POST)
        return super().get(request, *args, **kwargs)
