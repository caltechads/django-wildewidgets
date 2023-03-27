from copy import deepcopy
import datetime
import logging
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models.fields.related import RelatedField, ManyToManyRel

from .base import BaseDataTable
from .actions import ActionButtonBlockMixin, ActionsButtonsBySpecMixin, RowActionButton

logger = logging.getLogger(__name__)


# -------------------------------
# Mixins
# -------------------------------

class ModelTableMixin:
    """
    This mixin is used to create a table from a :py:class:`Model`.  It provides methods
    to create and configure columns based on model fields and configuration.

    Example::

        from django.db import models
        from wildewidgets import DataTable, ModelTableMixin

        class Author(models.Model):

            full_name = models.CharField(...)

        class Book(models.Model):

            title = models.CharField(...)
            isbn = models.CharField(...)
            authors = models.ManyToManyField(Author)

        class BookModelTable(ModelTableMixin, DataTable):

            model = Book

            fields = ['title', 'authors__full_name', 'isbn']
            alignment = {'authors': 'left'}
            verbose_names = {'authors__full_name': 'Authors'}
            buttons = True
            striped = True

            def render_authors__full_name_column(self, row, column):
                authors = row.authors.all()
                if authors.count() > 1:
                    return f"{authors[0].full_name} ... "
                return authors[0].full_name
    """

    #: The Django model class for this table
    model: Optional[Type[models.Model]]

    #: This is either ``None``, the string ``__all__`` or a list of column names
    #: to use in our table.  For the list, entries can either be field names
    #: from our :py:attr:`model`, or names of computed fields that will be
    #: rendered with a ``render_FIELD_column`` method.  If ``None``, empty list
    #: or ``__all__``, display all fields on the :py:attr:`model`.
    fields: Optional[Union[str, List[str]]] = []
    #: The list of field names to hide by default
    hidden: List[str] = []
    #: A mapping of field name to table column heading
    verbose_names: Dict[str, str] = {}
    #: A list of field names that will not be sortable
    unsortable: List[str] = []
    #: A list of field names that will not be searched when doing a global table search
    unsearchable: List[str] = []
    #: A mapping of field name to data type.  This is used to do some automatic formatting
    #: of table values.
    field_types: Dict[str, str] = {}
    #: A mapping of field name to field alignment.  Valid values are ``left``, ``right``, and
    #: ``center``
    alignment: Dict[str, str] = {}
    bool_icons = {}

    def __init__(
        self,
        *args,
        model: Optional[Type[models.Model]] = None,
        fields: Optional[Union[str, List[str]]] = None,
        hidden: List[str] = None,
        verbose_names: List[str] = None,
        unsortable: List[str] = None,
        unsearchable: List[str] = None,
        field_types: Dict[str, str] = None,
        alignment: Dict[str, str] = None,
        bool_icons: Dict[str, str] = None,
        **kwargs
    ):
        self.model = model if model is not None else self.model
        self.fields = fields if fields else deepcopy(self.fields)
        self.hidden = hidden if hidden else deepcopy(self.hidden)
        self.verbose_names = verbose_names if verbose_names else deepcopy(self.verbose_names)
        self.unsortable = unsortable if unsortable else deepcopy(self.unsortable)
        self.unsearchable = unsearchable if unsearchable else deepcopy(self.unsearchable)
        self.field_types = field_types if field_types else deepcopy(self.field_types)
        self.alignment = alignment if alignment else deepcopy(self.alignment)
        self.bool_icons = bool_icons if bool_icons else deepcopy(self.bool_icons)
        super().__init__(*args, **kwargs)

        #: A mapping of field name to Django field class
        self.model_fields: Dict[str, models.Field] = {}
        #: A mapping of field name to Django related field class
        self.related_fields: Dict[str, models.Field] = {}
        #: A list of names of our model fields
        self.field_names: List[str] = []

        # Build our mapping of all known fields on :py:attr:`model`
        for field in self.model._meta.get_fields():
            if field.name == 'id':
                continue
            self.model_fields[field.name] = field
            self.field_names.append(field.name)

        # Find our related fields -- these are in Django QuerySet format, e.g.
        # parent__child or parent__child__grandchild
        for field_name in self.fields:
            if field_name not in self.model_fields:
                field = self.get_related_field(self.model, field_name)
                if field:
                    self.related_fields[field_name] = field

        if not self.fields or self.fields == '__all__':
            self.load_all_fields()
        else:
            for field_name in self.fields:
                self.load_field(field_name)

    def get_related_model(
        self,
        current_model: Type[models.Model],
        field_name: str
    ) -> models.Model:
        return current_model._meta.get_field(field_name).related_model

    def get_related_field(
        self,
        current_model: models.Model,
        name: str
    ) -> Optional[models.Field]:
        """
        Given ``name``, a field specifier in Django QuerySet format, e.g.
        ``parent__child`` or ``parent__child__grandchild``, return the field
        instance that represents that field on the appropriate related model.

        Args:
            current_model:  the model for the leftmost field in ``name``
            name: the field specfier

        Returns:
            the :py:class:`Field` instance, or ``None`` if we couldn't find one.
        """
        name_fields: List[str] = name.split('__')
        if len(name_fields) == 1:
            # This is not a related field specifier
            return None
        # Walk through the fields and find the Django model for the last
        # field in the spec
        for field in name_fields[:-1]:
            current_model = self.get_related_model(current_model, field)
        if current_model:
            try:
                final_field = current_model._meta.get_field(name_fields[-1])
            except FieldDoesNotExist:
                final_field = None
        else:
            final_field = None
        return final_field

    def get_field(self, field_name: str) -> Optional[models.Field]:
        """
        Return the :py:class:`django.db.models.fields.Field` instance for the
        field named ``field_name``.  If no field with that name exists, return
        ``None``.

        Args:
            field_name: the name of the field to retrieve

        Returns:
            A django field instance, or ``None``.
        """
        if field_name in self.model_fields:
            field = self.model_fields[field_name]
        elif field_name in self.related_fields:
            field = self.related_fields[field_name]
        else:
            field = None
        return field

    def set_standard_column_attributes(self, field_name: str, kwargs: Dict[str, Any]) -> None:
        if field_name in self.hidden:
            kwargs['visible'] = False
        if field_name in self.unsearchable:
            kwargs['searchable'] = False
        if field_name in self.unsortable:
            kwargs['sortable'] = False
        if field_name in self.alignment:
            kwargs['align'] = self.alignment[field_name]
        else:
            field = self.get_field(field_name)
            if isinstance(field, (models.TextField, models.CharField, models.DateField, models.DateTimeField)):
                kwargs['align'] = 'left'
            else:
                kwargs['align'] = 'right'

    def load_field(self, field_name: str) -> None:
        if field_name in self.model_fields:
            field = self.model_fields[field_name]
            verbose_name = field.name.replace('_', ' ')
            kwargs = {}
            if field_name in self.verbose_names:
                kwargs['verbose_name'] = self.verbose_names[field_name]
            elif hasattr(field, 'verbose_name'):
                if verbose_name == field.verbose_name:
                    kwargs['verbose_name'] = verbose_name.capitalize()
                else:
                    kwargs['verbose_name'] = field.verbose_name
            self.set_standard_column_attributes(field_name, kwargs)
            self.add_column(field_name, **kwargs)
        else:
            kwargs = {}
            if field_name in self.verbose_names:
                verbose_name = self.verbose_names[field_name]
            else:
                verbose_name = field_name.replace('_', ' ').replace('__', ' ').capitalize()
            kwargs['verbose_name'] = verbose_name
            self.set_standard_column_attributes(field_name, kwargs)
            self.add_column(field_name, **kwargs)

    def load_all_fields(self) -> None:
        for field_name in self.field_names:
            self.load_field(field_name)

    def render_currency_type_column(self, value: Any) -> str:
        return f"${value}"

    def render_bool_type_column(self, value: Any) -> str:
        if value == "True":
            return '<i class="bi-check-lg text-success"><span style="display:none">True</span></i>'
        return ""

    def render_bool_icon_column(self, value: Any, icon_data: Tuple[str, str]) -> str:
        if len(icon_data) == 0:
            return value
        if value == "True":
            return f"<i class='bi-{icon_data[0][0]} {icon_data[0][1]}'><span style='display:none'>True</span></i>"
        if len(icon_data) > 1:
            return f"<i class='bi-{icon_data[1][0]} {icon_data[1][1]}'><span style='display:none'>False</span></i>"
        return ""

    def render_datetime_type_column(self, value: datetime.datetime) -> str:
        datetime_format = "%m/%d/%Y %H:%M"
        if hasattr(settings, 'WILDEWIDGETS_DATETIME_FORMAT'):
            datetime_format = settings.WILDEWIDGETS_DATETIME_FORMAT
        if value:
            return value.strftime(datetime_format)
        return ""

    def render_date_type_column(self, value: datetime.date) -> str:
        date_format = "%m/%d/%Y"
        if hasattr(settings, 'WILDEWIDGETS_DATE_FORMAT'):
            date_format = settings.WILDEWIDGETS_DATE_FORMAT
        if value:
            return value.strftime(date_format)
        return ""

    def render_column(self, row: Any, column: str) -> str:
        value = super().render_column(row, column)
        if column in self.model_fields:
            field = self.model_fields[column]
        elif column in self.related_fields:
            field = self.related_fields[column]
        else:
            field = None
        if column in self.field_types:
            field_type = self.field_types[column]
            attr_name = f"render_{field_type}_type_column"
            if hasattr(self, attr_name):
                if attr_name in ['date', 'datetime']:
                    value = getattr(row, column)
                return getattr(self, attr_name)(value)
        elif isinstance(field, models.DateTimeField):
            return self.render_datetime_type_column(getattr(row, column))
        elif isinstance(field, models.DateField):
            return self.render_date_type_column(getattr(row, column))
        elif column in self.bool_icons:
            return self.render_bool_icon_column(value, self.bool_icons[column])
        return value


class WidgetCellMixin:
    """
    This mixin is used to display a widget in a cell based on the value of the
    column.
    """

    # Specify the widget to use for each column. The key is the column name
    # and the value is the widget class. The widget class must be a subclass
    # of :py:class:`wildewidgets.widgets.base.Block`. Fields that are not specified
    # will not have a widget, but will be displayed as text.
    cell_widgets: Dict[str, str] = {}

    def render_column(self, row: Any, column: str) -> str:
        if column in self.cell_widgets:
            widget_class = self.cell_widgets[column]
            widget = widget_class(row=row, column=column)
            return str(widget)
        return super().render_column(row, column)


# -------------------------------
# Tables
# -------------------------------

class DataTable(
    ActionsButtonsBySpecMixin,
    BaseDataTable
):
    pass


class BasicModelTable(ModelTableMixin, DataTable):
    """
    This class is used to create a table from a
    :py:class:`django.db.models.Model`.  It provides a full featured table with
    a minimum of code. Many derived classes will only need to define class
    variables.

    Example::

        class BookModelTable(BasicModelTable):
            fields = ['title', 'authors__full_name', 'isbn']
            model = Book
            alignment = {'authors': 'left'}
            verbose_names = {'authors__full_name': 'Authors'}
            buttons = True
            striped = True

            def render_authors__full_name_column(self, row, column):
                authors = row.authors.all()
                if authors.count() > 1:
                    return f"{authors[0].full_name} ... "
                return authors[0].full_name
    """
    pass


class ActionButtonModelTable(
    ActionButtonBlockMixin,
    ModelTableMixin,
    BaseDataTable
):
    """
    This class is used to create a table from a
    :py:class:`django.db.models.Model`, and allows you to specify per-row actions
    as :py:class:`wildewidgets.widgets.tables.actions.RowActionButton` classes or
    subclasses.

    Example::

        class BookModelTable(ActionButtonModelTable):
            fields = ['title', 'authors__full_name', 'isbn']
            model = Book
            alignment = {'authors': 'left'}
            verbose_names = {'authors__full_name': 'Authors'}
            striped = True

            actions = [
                RowModelUrlButton(text='Edit', color='primary', attribute='get_absolute_url')
            ]

            def render_authors__full_name_column(self, row, column):
                authors = row.authors.all()
                if authors.count() > 1:
                    return f"{authors[0].full_name} ... "
                return authors[0].full_name
    """
    pass


class StandardActionButtonModelTable(
    ActionButtonBlockMixin,
    ModelTableMixin,
    BaseDataTable
):
    """
    This class is used to create a table from a
    :py:class:`django.db.models.Model`, and allows you to specify per-row
    actions as :py:class:`wildewidgets.widgets.tables.actions.RowActionButton`
    classes or subclasses.  An "Edit" and "Delete" button will be created for
    each row automatically.

    Important:

        For the buttons to work, use the
        :py:class:`wildewidgets.models.ViewSetMixin` on your model, and
        define the ``get_update_url`` and ``get_delete_url`` methods.

    Example::

        from django.db import models
        from django.urls import reverse
        from wildewdigets.models import ViewSetMixin
        from wildewidgets import StandardActionButtonModelTable

        class Book(ViewSetMixin, models.Model):

            title = models.CharField('Title', ...)
            isbn = models.CharField('ISBN', ...)
            publisher = models.CharField('Publisher', ...)
            num_pages = models.IntegerField('# Pages', ...)

            def get_update_url(self):
                return reverse('core:book--edit', args=[self.id])

            def get_delete_url(self):
                return reverse('core:book--delete', args=[self.id])


        class BookModelTable(StandardActionButtonModelTable):
            fields = ['title', 'publisher', 'isbn', 'num_pages']
            model = Book
            striped = True
    """
    pass


class LookupModelTable(
    ActionButtonBlockMixin,
    ModelTableMixin,
    BaseDataTable
):
    """
    This class is used to create a table for a lookup table.  It from
    :py:class:`ActionButtonsModelTable` in that if :py:attr:`fields` is empty,
    we'll build our ``fields`` list such that:

    * Only non-related fields are shown in the table
    * the ``id`` column is left aligned

    """

    actions: List[RowActionButton] = []

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', [])
        model = kwargs.get('model')
        if not model:
            model = self.model
        if not fields and not self.fields:
            alignment = {}
            fields = []
            for field in model._meta.get_fields():
                if not isinstance(field, (RelatedField, ManyToManyRel)):
                    # Exclude any RelatedField -- that's what
                    fields.append(field.name)
                    if field.name == 'id':
                        alignment['id'] = 'left'
            kwargs['fields'] = fields
            kwargs['alignment'] = alignment
        super().__init__(*args, **kwargs)
