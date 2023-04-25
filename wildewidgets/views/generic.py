from copy import deepcopy
import logging
from typing import Any, Dict, List, Optional, Type

from braces.views import (
    FormInvalidMessageMixin,
    FormValidMessageMixin,
    LoginRequiredMixin,
    MessageMixin
)
from django.forms import BaseModelForm, Form
from django.http.response import HttpResponse
from django.shortcuts import redirect
from django.views.generic import (
    CreateView as DjangoCreateView,
    TemplateView,
    UpdateView as DjangoUpdateView,
    View
)
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
from ..views import WidgetInitKwargsMixin, TableActionFormView
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
    WidgetListLayoutHeader
)

from .mixins import StandardWidgetMixin
from .permission import PermissionRequiredMixin


logger = logging.getLogger(__name__)


# --------------------------------------------
# Abastract Widgets
# --------------------------------------------

class AbstractFormPageLayout(Block):
    """
    This is a abstact class for making whole page layouts for a form page:
    creating or updating a model.

    It defines a page title, a page subtitle and a block to contain our
    main page content (typically just our model form).

    Subclass this and override :py:meth:`get_form` to render your main
    page content.

    Note:
        This class will try to supply a reasonable :py:attr:`title` and
        :py:attr:`subtitle`, by inferring reasonable values based on what base
        classes are in the ``view`` class hierarchy.  So you only need to set
        those if you don't get a title/subtitle that you like.

    Args:
        view: the view instance that will render this layout

    Keyword Args:
        title: use this as our page title
        subitle: Use this as our page subtitle.  This will appear directly
            below the page title.  Typically set this to a string naming the
            object we're updating
    """

    block: str = 'form-layout'

    #: Use this as our page ittle
    title: Optional[str] = None
    #: Use this as our page subtitle.  This will appear directly below
    #: the page title.  Typically set this to a string naming the object
    #: we're updating
    subtitle: Optional[str] = None

    def __init__(
        self,
        view: "GenericViewMixin",
        title: str = None,
        subtitle: str = None,
        **kwargs
    ):
        self.view = view
        self.title = title if title else self.title
        self.subtitle = subtitle if subtitle else self.subtitle
        if not self.title:
            if isinstance(self.view, DjangoCreateView):
                self.title = f'Create {self.view.model_verbose_name}'
            elif isinstance(self.view, DjangoUpdateView):
                self.title = f'Update {self.view.model_verbose_name}'
            else:
                self.title = f'Manage {self.view.model_verbose_name}'
        if not self.subtitle and view.object is not None:
            self.subtitle = str(view.object)
        super().__init__(**kwargs)
        self.add_block(self.get_title())
        if self.subtitle:
            self.add_block(self.get_subtitle())
        self.add_block(self.get_form())

    def get_title(self) -> Block:
        title = Block(
            self.title,
            name=f'{self.block}__title',
            tag='h1',
        )
        if not self.subtitle:
            title.add_class('mb-5')
        return title

    def get_subtitle(self) -> Optional[Block]:
        return Block(
            self.subtitle,
            name=f'{self.block}__subtitle',
            css_class='text-muted fs-6 text-uppercase mb-5'
        )

    def get_form(self) -> Block:
        raise NotImplementedError


# --------------------------------------------
# Widgets
# --------------------------------------------

class IndexTableWidget(Block):
    """
    This is the block that we use to render the listing table on the
    :py:class:`IndexView`.  It adds a header above the table.
    """

    def __init__(
        self,
        instance: ViewSetMixin,
        table: BaseDataTable,
        show_create_button: bool = True,
        **kwargs
    ):
        self.instance = instance
        self.show_create_button = show_create_button
        super().__init__(**kwargs)
        self.add_block(self.get_title())
        self.add_block(CardWidget(widget=table))

    def get_title(self) -> WidgetListLayoutHeader:
        header = WidgetListLayoutHeader(
            header_text=self.instance._meta.verbose_name_plural.capitalize(),
            badge_text=self.instance.objects.count(),
        )
        if self.show_create_button:
            header.add_link_button(
                text=f"New {self.instance._meta.verbose_name.capitalize()}",
                color="primary",
                url=self.instance.get_create_url()
            )
        return header


class FormPageLayout(AbstractFormPageLayout):

    left_column_width: int = 9

    def get_form(self) -> Block:
        layout = TwoColumnLayout(left_column_width=9)
        form_widget = CrispyFormWidget(
            form=self.view.get_form(),
            css_class='shadow bg-white p-4'
        )
        layout.add_to_left(form_widget)
        return layout


# --------------------------------------------
# View mixins
# --------------------------------------------

class GenericViewMixin:
    """
    This class based view mixin adds some methods and attributes that our
    other generic views use.
    """

    #: Set this to the model permissions the user must have in order
    #: to be authorized for this view:
    required_model_permissions: List[str] = []
    #: Set this to the logger of your choice
    logger: Any = logger
    #: Set this to your :py:class:`wildewidgets.widgets.navigation.BreadcrumbBlock`
    #: to manage breadcrumbs automatically.
    breadcrumbs: Optional[BreadcrumbBlock] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.breadcrumbs is not None:
            self.breadcrumbs = deepcopy(self.breadcrumbs)

    @property
    def model_name(self) -> str:
        """
        Return our model name.
        """
        if hasattr(self.model, 'model_name'):
            return self.model.model_name()
        return model_name(self.model)

    @property
    def model_logger_name(self) -> str:
        """
        Return a string we can use to identify this model in a log message.
        """
        if hasattr(self.model, 'model_logger_name'):
            return self.model.model_logger_name()
        return model_logger_name(self.model)

    @property
    def model_verbose_name(self) -> str:
        """
        Return a string we can use to identify this model in a log message.
        """
        if hasattr(self.model, 'model_verbose_name'):
            return self.model.model_verbose_name()
        return model_verbose_name(self.model)

    @property
    def model_verbose_name_plural(self) -> str:
        if hasattr(self.model, 'model_verbose_name_plural'):
            return self.model.model_verbose_name_plural()
        return model_verbose_name_plural(self.model)

    def get_client_ip(self) -> str:
        """
        Return our user's IP address.  This will either be the leftmost
        IP address in our ``X-Forwarded-For`` header, or the ``REMOTE_ADDR``
        header.

        Returns:
            Our user's IP address
        """
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return self.request.META.get('REMOTE_ADDR')

    @property
    def logging_extra(self) -> str:
        """
        Build some extra stuff to append to our logging statements:

        * add the user's remote_ip
        * add the user's username
        * add the pk of the object, if any

        Returns:
            A string to append to our log message
        """
        data = {}
        data['remote_ip'] = self.get_client_ip()
        data['username'] = self.request.user.username
        if hasattr(self, 'object'):
            data['pk'] = self.object.pk
        return ' '.join([f'{key}={value}' for key, value in data.items()])

    def get_menu_item(self) -> Optional[str]:
        """
        Return the name of the main menu item to set active, which is the
        the appropriately capitalized ``verbose_name_plural`` for our model.

        Returns:
            The name of the main menu item to set active.
        """
        return self.model_verbose_name_plural

    def get_permissions_required(self) -> List[str]:
        """
        Overrides :py:meth:`wildewidgets.views.permission.PermissionRequiredMixin.get_permissions_required`.

        Expand the permissions listed in :py:attr:`required_model_permissions`
        into full Django permission strings (e.g. ``appname.add_modelname`` and
        add them to the list of permissions already defined by our superclass.

        Returns:
            The list of Django user permission strings
        """
        required_perms = set(super().get_permissions_required())
        required_perms.update(
            self.get_model_permissions(self.model, self.required_model_permissions)
        )
        return list(required_perms)

    def get_breadcrumbs(self) -> "Optional[BreadcrumbBlock]":
        """
        Add our title to the breadcrumbs and return the updated block.

        Returns:
            The breadcrumb block to use
        """
        if self.breadcrumbs:
            self.breadcrumbs.add_breadcrumb(title=self.get_title())
        return self.breadcrumbs


class GenericDatatableMixin:

    model: Optional[Type[ViewSetMixin]]

    #: The :py:class:`wildewidgets.widgets.tables.base.BaseDataTable` subclass
    #: to use for the listing table
    table_class: Type[BaseDataTable] = LookupModelTable
    #: A dictionary that we will use as the ``**kwargs`` for the constructor of
    #: :py:attr:`table_class`
    table_kwargs: Dict[str, Any] = {
        'striped': True,
        'page_length': 25,
        'buttons': True,
    }

    def get_table_kwargs(self) -> Dict[str, Any]:
        """
        Return a dict that will be used as the ``**kwargs`` for constructing our
        :py:attr:`table_class` instance.

        If there are no bulk_action form actions defined, define one for bulk
        deleting rows.

        Returns:
            Constructor kwargs for :py:class:`table_class`
        """
        table_kwargs = self.table_kwargs
        if 'form_actions' not in table_kwargs and self.bulk_action_url_name:
            table_kwargs['form_actions'] = [
                ('delete', f'Delete {self.model_verbose_name}')
            ]

        return table_kwargs

    def get_table(self, *args, **kwargs) -> BaseDataTable:
        kwargs.update(self.get_table_kwargs())
        kwargs['model'] = self.model
        actions = []
        if self.user_can_update():
            actions.append(RowEditButton())
        if self.user_can_delete():
            actions.append(RowDeleteButton())
        if actions:
            kwargs['actions'] = actions
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
    TemplateView
):

    #: The model we're describing in this view. It must have
    #: :py:class:`wildewidgets.models.ViewSetMixin` in its class heirarchy
    model: Optional[Type[ViewSetMixin]] = None

    required_model_permissions: List[str] = ['view', 'add', 'change', 'delete']

    def get_title(self) -> str:
        """
        Return our page title.

        Returns:
            The string to use as our page title.
        """
        return self.model_verbose_name_plural

    def get_content(self) -> Widget:
        return IndexTableWidget(
            self.model,
            self.get_table(),
            show_create_button=self.user_can_create()
        )


class TableAJAXView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    WidgetInitKwargsMixin,
    GenericDatatableMixin,
    View
):
    #: The model we're describing in this view. It must have
    #: :py:class:`wildewidgets.models.ViewSetMixin` in its class heirarchy
    model: Optional[Type[ViewSetMixin]] = None

    required_model_permissions: List[str] = ['view', 'add', 'change', 'delete']

    def dispatch(self, request, *args, **kwargs):
        csrf_token = request.GET.get('csrf_token', '')
        extra_data = self.get_decoded_extra_data(request)
        initargs = extra_data.get('args', [])
        initkwargs = extra_data.get('kwargs', {})
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
    TableActionFormView
):
    #: The model we're describing in this view. It must have
    #: :py:class:`wildewidgets.models.ViewSetMixin` in its class heirarchy
    model: Optional[Type[ViewSetMixin]] = None

    #: Set this to the logger of your choice
    logger: Any = logger

    required_model_permissions: List[str] = ['delete']

    def process_delete_action(self, items: List[str]) -> None:
        qs = self.model.objects.filter(id__in=items)
        count = qs.count()
        qs.delete()
        self.logger.info(
            '%s.bulk.delete ids=%s %s',
            self.model_logger_name,
            ','.join(items),
            self.logging_extra
        )
        self.messages.success(f'Deleted {count} {self.model.model_verbose_name_plural()}.')


class CreateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    FormInvalidMessageMixin,
    FormValidMessageMixin,
    GenericViewMixin,
    NavbarMixin,
    StandardWidgetMixin,
    DjangoCreateView
):

    required_model_permissions: List[str] = ['add']

    #: Use this :py:class:`AbstractFormPageLayout` subclass to render our page
    layout_widget: Type[AbstractFormPageLayout] = FormPageLayout

    def get_form_invalid_message(self):
        self.logger.warning(
            '%s.create.failed.validation %s',
            self.model_logger_name,
            self.logging.extra
        )
        return f"Couldn't create this {self.model_verbose_name} due to validation errors; see below."

    def get_form_valid_message(self):
        self.logger.info('%s.create.success %s', self.model_logger_name, self.logging_extra)
        return f'Created {self.model_verbose_name} "{str(self.object)}"!'

    def get_form_class(self) -> Type[BaseModelForm]:
        # FIXME: this is probably not the right way to do this.  I'd like it
        # that if there is a form_class defined on us, use that otherwise ask
        # the model
        if hasattr(self.model, 'get_create_form_class'):
            return self.model.get_create_form_class()
        return super().get_form_class()

    def get_title(self) -> str:
        """
        Return our page title.

        Returns:
            The string to use as our page title.
        """
        return f'Create {self.model_verbose_name}'

    def get_content(self) -> Widget:
        return self.layout_widget(self, modifier='create')


class UpdateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    FormInvalidMessageMixin,
    FormValidMessageMixin,
    GenericViewMixin,
    NavbarMixin,
    StandardWidgetMixin,
    DjangoUpdateView
):

    required_model_permissions: List[str] = ['change']

    #: Use this :py:class:`AbstractFormPageLayout` subclass to render our page
    layout_widget: Type[AbstractFormPageLayout] = FormPageLayout

    def get_form_invalid_message(self):
        self.logger.warning(
            '%s.update.failed.validation %s',
            self.model_logger_name,
            self.logging.extra
        )
        return f"Couldn't update this {self.model_verbose_name} due to validation errors; see below."

    def get_form_valid_message(self):
        self.logger.info('%s.update.success %s', self.model_logger_name, self.logging_extra)
        return f'Updated {self.model_verbose_name} "{str(self.object)}"!'

    def get_form_class(self) -> Type[BaseModelForm]:
        # FIXME: this is probably not the right way to do this.  I'd like it
        # that if there is a form_class defined on us, use that otherwise ask
        # the model
        if hasattr(self.object, 'get_update_form_class'):
            return self.object.get_update_form_class()
        return super().get_form_class()

    def get_title(self) -> str:
        """
        Return our page title.

        Returns:
            The string to use as our page title.
        """
        return f'Update {self.model_verbose_name} "{str(self.object)}"'

    def get_content(self) -> Widget:
        return self.layout_widget(self, modifier='update')


class DeleteView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    GenericViewMixin,
    FormInvalidMessageMixin,
    FormValidMessageMixin,
    BaseDeleteView
):

    model: Optional[Type[ViewSetMixin]] = None

    http_method_names: List[str] = ['post']

    required_model_permissions: List[str] = ['delete']

    def get_form_invalid_message(self):
        self.logger.warning('%s.delete.failed.validation', self.model_logger_name)
        return f'Couldn\'t delete {self.model_verbose_name} "{str(self.object)}"'

    def get_form_valid_message(self):
        self.logger.info('%s.delete.success %s', self.model_logger_name, self.logging_extra)
        return f'Deleted {self.model_verbose_name} "{str(self.object)}"!'

    def form_invalid(self, form: BaseModelForm) -> HttpResponse:
        return redirect(self.get_success_url())

    def get_form_class(self) -> Type[BaseModelForm]:
        # FIXME: this is probably not the right way to do this.  I'd like it
        # that if there is a form_class defined on us, use that otherwise ask
        # the model
        if hasattr(self.object, 'get_delete_form_class'):
            return self.object.get_delete_form_class()
        return super().get_form_class()


class ManyToManyRelatedFieldView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    FormValidMessageMixin,
    MessageMixin,
    GenericViewMixin,
    BaseUpdateView
):

    field_name: Optional[str] = None
    form_class: Type[AbstractRelatedFieldForm] = ToggleableManyToManyFieldForm

    required_model_permissions: List[str] = ['change']

    @property
    def model_logger_name(self) -> str:
        return f'{super().model_logger_name}.{self.field_name}'

    @property
    def field_verbose_name(self) -> str:
        return self.model._meta.get_field(self.field_name).verbose_name.capitalize()

    def get_form_kwargs(self) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs['field_name'] = self.field_name
        return kwargs

    def form_invalid(self, form: Form) -> HttpResponse:
        self.logger.warning(
            '%s.update.failed.validation %s',
            self.model_logger_name,
            self.logging.extra
        )
        self.messages.error(
            f'Couldn\'t update {self.field_verbose_name} on {self.model_verbose_name} "{str(self.object)}"'
        )
        for k, errors in form.errors.as_data().items():
            for error in errors:
                self.messages.error(f"{k}: {error.message}")
        return redirect(self.get_success_url())

    def get_form_valid_message(self):
        self.logger.info('%s.update.success %s', self.model_logger_name, self.logging_extra)
        return f'Updated {self.field_verbose_name} on {self.model_verbose_name} "{str(self.object)}"!'

    def get_success_url(self) -> str:
        success_url = super().get_success_url()
        if not success_url:
            if hasattr(object, 'get_update_url'):
                return self.object.get_update_url()
            return self.object.get_absolute_url()
        return success_url


class HTMXView(TemplateView):
    """
    Simple view to display only a widget as a response. This is useful for
    HTMX requests. The widget is rendered with the context data from the
    request, such that anything sent via GET or POST is passed as kwargs to
    the widget's constructor.

    Example:

        class MyWidgetHTMXView(HTMXView):
            widget_class = MyWidget
    """
    template_name = 'wildewidgets/htmx_base.html'
    widget_class = None
    include_request = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = None

    def get_content(self, **kwargs):
        if self.widget_class:
            if self.include_request:
                self.data['request'] = self.request
            return self.widget_class(**self.data)
        raise NotImplementedError

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content'] = self.get_content(**self.data)
        return context

    def set_data(self, request_data):
        self.data = request_data.dict()
        del self.data['submit']

    def get(self, request, *args, **kwargs):
        self.set_data(request.GET)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.set_data(request.POST)
        return self.get(request, *args, **kwargs)
