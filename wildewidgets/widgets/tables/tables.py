from __future__ import annotations

import logging
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Literal, cast

from django.conf import settings
from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.db import models
from django.db.models.fields.related import ManyToManyRel, RelatedField

from .actions import (
    ActionButtonBlockMixin,
    ActionsButtonsBySpecMixin,
    RowActionButton,
)
from .base import BaseDataTable

if TYPE_CHECKING:
    import datetime

    from django.contrib.contenttypes.fields import GenericForeignKey

    from ..base import Widget

logger = logging.getLogger(__name__)


# -------------------------------
# Mixins
# -------------------------------


class ModelTableMixin:
    """
    Mixin used to create a table from a Django Model with automatic column
    configuration.

    This mixin automatically discovers model fields and creates appropriate
    table columns with sensible defaults for alignment, sorting, and display
    formatting. It handles both direct model fields and related fields through
    Django's double-underscore notation.

    Important:
        Typically you will not use this directly in your code, but instead use
        one of the pre-defined table classes like :py:class:`BasicModelTable`,
        :py:class:`ActionButtonModelTable`, or
        :py:class:`StandardActionButtonModelTable`.

    Notes:
        - Django ``DateField`` and ``DateTimeField`` fields are automatically
          formatted using the ``WILDEWIDGETS_DATE_FORMAT`` and ``
          WILDEWIDGETS_DATETIME_FORMAT`` settings.
        - Django ``BooleanField`` fields can be rendered with custom icons using
          the ``bool_icons`` attribute, which maps field names to tuples of icon
          specifications.
        - For the ``field_types`` attribute/kwarg, currently available choices for
          the dict values are:

          * ``date``: For formatting date fields
          * ``datetime``: For formatting datetime fields
          * ``currency``: For formatting currency values with a dollar sign
          * ``bool``: For rendering boolean values as check icons

        - You may add a new field type by implementing a method named
          ``render_FIELD_type_column`` on your table class, where
          ``FIELD`` is the name of the field type (e.g.,
          ``render_currency_type_column``)

    Example:
        .. code-block:: python

            from django.db import models
            from django.contrib.contenttypes.fields import GenericForeignKey
            from wildewidgets.widgets.tables import ModelTableMixin, DataTable

            class Author(models.Model):
                full_name = models.CharField(max_length=100)

            class Book(models.Model):
                title = models.CharField(max_length=200)
                authors = models.ManyToManyField(Author, related_name='books')
                isbn = models.CharField(max_length=20)
                published_date = models.DateField()

            # Example table using ModelTableMixin

            class BookTable(ModelTableMixin, DataTable):
                model = Book
                fields = ['title', 'authors__full_name', 'isbn', 'published_date']
                alignment = {'isbn': 'center', 'published_date': 'right'}
                verbose_names = {'authors__full_name': 'Authors'}
                field_types = {'published_date': 'date'}

                def render_authors__full_name_column(self, row, column):
                    return ", ".join([a.full_name for a in row.authors.all()])

    Args:
        *args: Variable length argument list (unused)

    Keyword Args:
        model: The Django model class to use for this table.  If not provided,
            the :py:attr:`model` attribute must be set on the class.
        fields: A list of field names to include in the table.  If not provided,
            defaults to all fields on the model.  The ``fields`` attribute can be set to
            ``None``, an empty list, or the string `"__all__"` to include all
            fields on the model. If a list is provided, it can include related fields
            using Django's double-underscore notation (e.g., `authors__full_name`).
        hidden: A list of field names to hide by default.  Users can unhide fields via
            the table controls.
        verbose_names: A dictionary mapping field names to custom column headers where
            the key is the field name and the value is the desired header text.
        unsortable: A list of field names that will not be sortable.  This means
            that the up/down arrows will not be displayed in the table header
            for these fields, and they will not be included in the sort query.
        unsearchable: A list of field names that will not be searched when doing
            a global table search.  This means the field will not be included
            in the search query, but it will still be displayed in the table.
        field_types: A dictionary mapping field names to data types for automatic
            formatting of table values.
        alignment: A dictionary mapping field names to alignment values. Valid
            values are ``left``, ``right``, and ``center``.  The key is the field name
            and the value is the alignment value.  If not provided, defaults to
            ``left`` for all text fields and ``right`` for numeric fields.
        bool_icons: A dictionary mapping field names to tuples of icon specifications
            for rendering boolean values. Each tuple should contain 1-2 icon specs:
            (icon_name, css_class) for True and optionally (icon_name,
            css_class) for False.

    Raises:
        ImproperlyConfigured: If the model is not set and no model is provided
            during initialization.
        django.core.exceptions.FieldDoesNotExist: If a specified field does not exist
            on the model or related models.

    """

    #: The Django model class for this table
    model: type[models.Model] | None = None

    #: This is either ``None``, the string ``__all__`` or a list of column names
    #: to use in our table.  For the list, entries can either be field names
    #: from our :py:attr:`model`, or names of computed fields that will be
    #: rendered with a ``render_FIELD_column`` method.  If ``None``, empty list
    #: or ``__all__``, display all fields on the :py:attr:`model`.
    fields: str | list[str] | None = []  # noqa: RUF012
    #: The list of field names to hide by default
    hidden: list[str] = []  # noqa: RUF012
    #: A mapping of field name to table column heading
    verbose_names: dict[str, str] = {}  # noqa: RUF012
    #: A list of field names that will not be sortable
    unsortable: list[str] = []  # noqa: RUF012
    #: A list of field names that will not be searched when doing a global table search
    unsearchable: list[str] = []  # noqa: RUF012
    #: A mapping of field name to data type.  This is used to do some automatic
    #: formatting of table values.
    field_types: dict[str, str] = {}  # noqa: RUF012
    #: A mapping of field name to field alignment.  Valid values are ``left``,
    #: ``right``, and : ``center``
    alignment: dict[str, Literal["left", "right", "center"]] = {}  # noqa: RUF012
    bool_icons: dict[str, tuple[tuple[str, str], ...]] = {}  # noqa: RUF012

    def __init__(
        self,
        *args,
        model: type[models.Model] | None = None,
        fields: str | list[str] | None = None,
        hidden: list[str] | None = None,
        verbose_names: dict[str, str] | None = None,
        unsortable: list[str] | None = None,
        unsearchable: list[str] | None = None,
        field_types: dict[str, str] | None = None,
        alignment: dict[str, Literal["left", "right", "center"]] | None = None,
        bool_icons: dict[str, tuple[tuple[str, str], ...]] | None = None,
        **kwargs,
    ):
        self.model = model if model is not None else self.model
        if not self.model:
            msg = f"{self.__class__.__name__} requires a model to be set"
            raise ImproperlyConfigured(msg)
        self.fields = fields if fields else deepcopy(self.fields)
        self.hidden = hidden if hidden else deepcopy(self.hidden)
        self.verbose_names = (
            verbose_names if verbose_names else deepcopy(self.verbose_names)
        )
        self.unsortable = unsortable if unsortable else deepcopy(self.unsortable)
        self.unsearchable = (
            unsearchable if unsearchable else deepcopy(self.unsearchable)
        )
        self.field_types = field_types if field_types else deepcopy(self.field_types)
        self.alignment = alignment if alignment else deepcopy(self.alignment)
        self.bool_icons = bool_icons if bool_icons else deepcopy(self.bool_icons)
        super().__init__(*args, **kwargs)

        #: A mapping of field name to Django field class
        self.model_fields: dict[
            str, models.Field | models.ForeignObjectRel | GenericForeignKey
        ] = {}
        #: A mapping of field name to Django related field class
        self.related_fields: dict[
            str, models.Field | models.ForeignObjectRel | GenericForeignKey
        ] = {}
        #: A list of names of our model fields
        self.field_names: list[str] = []

        # Build our mapping of all known fields on :py:attr:`model`
        for field in cast("models.Model", self.model)._meta.get_fields():
            if field.name == "id":
                continue
            self.model_fields[field.name] = field
            self.field_names.append(field.name)

        # Find our related fields -- these are in Django QuerySet format, e.g.
        # parent__child or parent__child__grandchild
        if isinstance(self.fields, list):
            for field_name in self.fields:
                if field_name not in self.model_fields:
                    _field = self.get_related_field(
                        cast("type[models.Model]", self.model), field_name
                    )
                    if _field:
                        self.related_fields[field_name] = _field

        if not self.fields or self.fields == "__all__":
            self.load_all_fields()
        else:
            for field_name in self.fields:
                self.load_field(field_name)

    def get_related_model(
        self, current_model: type[models.Model], field_name: str
    ) -> type[models.Model] | None:
        """
        Get the related model for a relationship field.

        Args:
            current_model: The model containing the relationship field
            field_name: The name of the relationship field

        Returns:
            The related model class or None if not found

        """
        return current_model._meta.get_field(field_name).related_model

    def get_related_field(
        self, current_model: type[models.Model], name: str
    ) -> models.Field | models.ForeignObjectRel | GenericForeignKey | None:
        """
        Resolve a field from a related model using Django's double-underscore notation.

        This method handles field paths like 'author__publisher__name' by traversing
        the model relationships to find the final field object.

        Args:
            current_model: The starting model class
            name: Field path using Django's double-underscore notation

        Returns:
            The Django Field instance for the final field in the path, or None
            if not found

        Example:
            For a path 'author__publisher__name', this would:

            1. Get the 'author' field from the current model
            2. Get the related model (Publisher)
            3. Return the 'name' field from the Publisher model

        """
        name_fields: list[str] = name.split("__")
        if len(name_fields) == 1:
            # This is not a related field specifier
            return None
        # Walk through the fields and find the Django model for the last
        # field in the spec
        for field in name_fields[:-1]:
            related_model_class = self.get_related_model(current_model, field)
            if not related_model_class:
                return None
            current_model = related_model_class
        if current_model:
            try:
                final_field = current_model._meta.get_field(name_fields[-1])
            except FieldDoesNotExist:
                final_field = None
        else:
            final_field = None
        return final_field

    def get_field(
        self, field_name: str
    ) -> models.Field | models.ForeignObjectRel | GenericForeignKey | None:
        """
        Get a field instance by name, checking both direct and related fields.

        Args:
            field_name: The name of the field to retrieve

        Returns:
            The Django Field instance or None if not found

        """
        if field_name in self.model_fields:
            field = self.model_fields[field_name]
        elif field_name in self.related_fields:
            field = self.related_fields[field_name]
        else:
            field = None
        return field

    def set_standard_column_attributes(
        self, field_name: str, kwargs: dict[str, Any]
    ) -> None:
        """
        Set standard column attributes based on field type and configuration.

        This method configures:

        - Visibility based on the 'hidden' list
        - Searchability based on the 'unsearchable' list
        - Sortability based on the 'unsortable' list
        - Alignment based on the 'alignment' dict or field type

        Args:
            field_name: The name of the field to configure
            kwargs: Dictionary of attributes to update

        """
        if field_name in self.hidden:
            kwargs["visible"] = False
        if field_name in self.unsearchable:
            kwargs["searchable"] = False
        if field_name in self.unsortable:
            kwargs["sortable"] = False
        if field_name in self.alignment:
            kwargs["align"] = self.alignment[field_name]
        else:
            field = self.get_field(field_name)
            if isinstance(
                field,
                (
                    models.TextField,
                    models.CharField,
                    models.DateField,
                    models.DateTimeField,
                ),
            ):
                kwargs["align"] = "left"
            else:
                kwargs["align"] = "right"

    def load_field(self, field_name: str) -> None:
        """
        Add a column for a single field to the table.

        This method handles field discovery, verbose name resolution, and column
        attribute configuration before adding the column to the table.

        Args:
            field_name: The name of the field to add as a column

        """
        if field_name in self.model_fields:
            field = self.model_fields[field_name]
            verbose_name = field.name.replace("_", " ")
            kwargs = {}
            if field_name in self.verbose_names:
                kwargs["verbose_name"] = self.verbose_names[field_name]
            elif hasattr(field, "verbose_name"):
                if verbose_name == field.verbose_name:
                    kwargs["verbose_name"] = verbose_name.capitalize()
                else:
                    kwargs["verbose_name"] = str(field.verbose_name)
            self.set_standard_column_attributes(field_name, kwargs)
            self.add_column(field_name, **kwargs)
        else:
            kwargs = {}
            if field_name in self.verbose_names:
                verbose_name = self.verbose_names[field_name]
            else:
                verbose_name = (
                    field_name.replace("_", " ").replace("__", " ").capitalize()
                )
            kwargs["verbose_name"] = verbose_name
            self.set_standard_column_attributes(field_name, kwargs)
            self.add_column(field_name, **kwargs)

    def load_all_fields(self) -> None:
        """
        Add columns for all discovered model fields to the table.

        This is called when fields="__all__" or when fields is empty.
        """
        for field_name in self.field_names:
            self.load_field(field_name)

    def render_currency_type_column(self, value: Any) -> str:
        """
        Format a value as currency with a dollar sign.

        Args:
            value: The value to format

        Returns:
            Formatted currency string with dollar sign

        """
        return f"${value}"

    def render_bool_type_column(self, value: Any) -> str:
        """
        Format a boolean value as a check icon for True values.

        Args:
            value: The boolean value to format

        Returns:
            HTML for a checkmark icon if True, empty string if False

        """
        if value == "True":
            return '<i class="bi-check-lg text-success"><span style="display:none">True</span></i>'  # noqa: E501
        return ""

    def render_bool_icon_column(
        self, value: Any, icon_data: tuple[tuple[str, str], ...]
    ) -> str:
        """
        Format a boolean value using custom icons.

        Args:
            value: The boolean value to format
            icon_data: Tuple of icon specifications (icon_name, css_class)

        Returns:
            HTML for the specified icon based on the boolean value

        Note:
            The icon_data tuple should contain 1-2 icon specifications:
            - First icon is used for True values
            - Second icon (if provided) is used for False values

        """
        if len(icon_data) == 0:
            return value
        if value == "True":
            return f"<i class='bi-{icon_data[0][0]} {icon_data[0][1]}'><span style='display:none'>True</span></i>"  # noqa: E501
        if len(icon_data) > 1:
            return f"<i class='bi-{icon_data[1][0]} {icon_data[1][1]}'><span style='display:none'>False</span></i>"  # noqa: E501
        return ""

    def render_datetime_type_column(self, value: datetime.datetime) -> str:
        """
        Format a datetime value with the configured datetime format.

        Args:
            value: The datetime value to format

        Returns:
            Formatted datetime string

        Note:
            The format can be customized using the `WILDEWIDGETS_DATETIME_FORMAT`
            setting in Django settings.

        """
        datetime_format = "%m/%d/%Y %H:%M"
        if hasattr(settings, "WILDEWIDGETS_DATETIME_FORMAT"):
            datetime_format = settings.WILDEWIDGETS_DATETIME_FORMAT
        if value:
            return value.strftime(datetime_format)
        return ""

    def render_date_type_column(self, value: datetime.date) -> str:
        """
        Format a date value with the configured date format.

        Args:
            value: The date value to format

        Returns:
            Formatted date string, optionally with title attribute for full date format

        Note:
            The format can be customized using the WILDEWIDGETS_DATE_FORMAT
            setting in Django settings.

        """
        date_format = "%m/%d/%Y"
        full_date_format = date_format
        modified_date_format = False
        if hasattr(settings, "WILDEWIDGETS_DATE_FORMAT"):
            date_format = settings.WILDEWIDGETS_DATE_FORMAT
            modified_date_format = True
        if value:
            date_str = value.strftime(date_format)
            if modified_date_format:
                full_date_str = value.strftime(full_date_format)
                return f"<span title='{full_date_str}'>{date_str}</span>"
            return date_str
        date_str = ""
        if modified_date_format:
            return f"<span title='{date_str}'>{date_str}</span>"
        return date_str

    def render_column(self, row: Any, column: str) -> str:
        """
        Render a cell value with appropriate formatting based on field type.

        This method handles special formatting for different field types:

        - Applies custom rendering for fields in field_types dictionary
        - Automatically formats DateTimeField and DateField values
        - Applies icon rendering for boolean fields in bool_icons dictionary

        Args:
            row: The data object for the current row
            column: The name of the column to render

        Returns:
            Formatted HTML string for the cell value

        """
        value = super().render_column(row, column)  # type: ignore[misc]
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
                if attr_name in ["date", "datetime"]:
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
    Mixin that enables using custom widgets to render individual table cells.

    This mixin allows you to specify custom widget classes for different columns,
    providing complete control over how cell data is rendered. Each widget receives
    the row data and column name, allowing for complex rendering based on the full
    context of the data.

    If a widget is defined for a column in the :py:attr:`cell_widgets` dictionary,
    it will be used to render the cell.  Otherwise, the standard column rendering
    will be used.

    Important:
        Cell widgets need to be :py:class:`wildewidgets.Block` subclasses that
        accept two additional keyword arguments:

        - row: The data object for the current row
        - column: The name of the column to render

        .. code-block:: python

            from wildewidgets import Block

            class MyCellWidget(Block):

                def __init__(self, row=None, column=None, **kwargs):
                    self.row = row
                    self.column = column
                    self.value = getattr(row, column)
                    super().__init__(f"Value is {self.value}", **kwargs)

    Attributes:
        cell_widgets: Dictionary mapping column names to widget classes for rendering
            cells in those columns

    Example:
        .. code-block:: python

            from wildewidgets import WidgetCellMixin, DataTable
            from wildewidgets.widgets.base import Block

            class StatusWidget(Block):
                def __init__(self, row=None, column=None, **kwargs):
                    super().__init__(**kwargs)
                    status = getattr(row, column)
                    if status == 'active':
                        self.add_class('badge bg-success')
                    elif status == 'pending':
                        self.add_class('badge bg-warning')
                    else:
                        self.add_class('badge bg-secondary')
                    self.text = status.capitalize()

            class MyTable(WidgetCellMixin, DataTable):
                cell_widgets = {
                    'status': StatusWidget
                }

    """

    #: Specify the widget to use for each column. The key is the column name
    #: and the value is the widget class. The widget class must be a subclass
    #: of :py:class:`wildewidgets.Block`. Fields that are not specified
    #: will not have a widget, but will be displayed as text.
    cell_widgets: dict[str, type[Widget]] = {}  # noqa: RUF012

    def render_column(self, row: Any, column: str) -> str:
        """
        Render a cell using a custom widget if defined for the column.

        If a widget is defined for the column in :py:attr:`cell_widgets`, this
        method instantiates the widget with the row and column data and returns
        its rendered output.  Otherwise, it falls back to the standard column
        rendering.

        Args:
            row: The data object for the current row
            column: The name of the column to render

        Returns:
            Rendered HTML string for the cell

        """
        if column in self.cell_widgets:
            widget_class = self.cell_widgets[column]
            widget = widget_class(row=row, column=column)
            return str(widget)
        return super().render_column(row, column)  # type: ignore[misc]


# -------------------------------
# Tables
# -------------------------------


class DataTable(ActionsButtonsBySpecMixin, BaseDataTable):  # type: ignore[misc]
    """
    Standard data table implementation with action buttons specs.

    This class combines :py:class:`BaseDataTable` with
    :py:class:`wildewidgets.ActionsButtonsBySpecMixin` to create a complete
    table implementation that supports all base table features plus action
    buttons for each row.

    Example:
        .. code-block:: python

            from wildewidgets.widgets.tables import DataTable

            class MyTable(DataTable):
                actions = [
                    ('Edit', 'my_app:edit'),
                    ('Delete', 'my_app:delete', 'post', 'danger')
                ]

                def get_queryset(self):
                    return MyModel.objects.all()

    """


class BasicModelTable(ModelTableMixin, DataTable):  # type: ignore[misc]
    """
    Ready-to-use table for displaying Django model data.

    This class combines :py:class:`ModelTableMixin` and :py:class:`DataTable` to
    provide a complete solution for displaying model data with minimal
    configuration. Simply define your model and field configuration as class
    attributes.

    Example:
        .. code-block:: python

            from django.db import models
            from wildewidgets.widgets.tables import BasicModelTable

            class Author(models.Model):
                full_name = models.CharField(max_length=100)

            class Book(models.Model):
                title = models.CharField(max_length=200)
                authors = models.ManyToManyField(Author, related_name='books')
                isbn = models.CharField(max_length=20)

            # Example table using BasicModelTable

            class BookTable(BasicModelTable):
                model = Book
                fields = ['title', 'authors__full_name', 'isbn']
                alignment = {'authors': 'left'}
                verbose_names = {'authors__full_name': 'Authors'}
                buttons = True
                striped = True

                def render_authors__full_name_column(self, row, column):
                    authors = row.authors.all()
                    if authors.count() > 1:
                        return f"{authors[0].full_name} + {authors.count()-1} more"
                    return authors[0].full_name if authors else ""

    """


class ActionButtonModelTable(ActionButtonBlockMixin, ModelTableMixin, BaseDataTable):  # type: ignore[misc]
    """
    Model table with customizable row action buttons.

    This class allows you to define action buttons for each row using
    :py:class:`RowActionButton` instances and subclasses, providing flexibility
    in button appearance and behavior. Buttons can perform different actions
    based on the row data, like linking to detail pages, opening modals, or
    submitting forms.

    Example:
        .. code-block:: python

            from django.db import models
            from wildewidgets import (
                ActionButtonModelTable,
                RowModelUrlButton,
                RowFormButton
            )

            class Author(models.Model):
                full_name = models.CharField(max_length=100)

            class Book(models.Model):
                title = models.CharField(max_length=200)
                authors = models.ManyToManyField(Author, related_name='books')
                isbn = models.CharField(max_length=20)

                def get_absolute_url(self):
                    return f"/books/{self.id}/"

                def get_delete_url(self):
                    return f"/books/{self.id}/delete/"

            class BookTable(ActionButtonModelTable):
                model = Book
                fields = ['title', 'authors__full_name', 'isbn']
                verbose_names = {'authors__full_name': 'Authors'}

                actions = [
                    RowModelUrlButton(
                        text='View',
                        color='primary',
                        attribute='get_absolute_url'
                    ),
                    RowFormButton(
                        text='Delete',
                        color='danger',
                        attribute='get_delete_url',
                        form_fields=['id'],
                        confirm_text='Are you sure you want to delete this book?'
                    )
                ]

    """


class StandardActionButtonModelTable(  # type: ignore[misc]
    ActionButtonBlockMixin, ModelTableMixin, BaseDataTable
):  # type: ignore[misc]
    """
    Model table with standard "Edit" and "Delete" buttons for each row.

    This class provides a convenient implementation for the common pattern of
    displaying model data with "Edit" and "Delete" actions. It automatically creates
    these buttons and links them to the appropriate URLs from your model.

    Requirements:
        - Your model must have the :py:class:`wildewidgets.ViewSetMixin` mixin in
          its inheritance chain
        - Your model must implement ``get_absolute_url``, ``get_update_url`` and
          ``get_delete_url`` methods

    Attributes:
        model: The Django model class to display
        fields: List of fields to include in the table

    Example:
        .. code-block:: python

            from django.db import models
            from django.urls import reverse
            from wildewidgets.models import ViewSetMixin

            class Book(ViewSetMixin, models.Model):
                title = models.CharField('Title', max_length=100)
                isbn = models.CharField('ISBN', max_length=20)

                def get_absolute_url(self):
                    return reverse('books:detail', args=[self.id])

                def get_update_url(self):
                    return reverse('books:edit', args=[self.id])

                def get_delete_url(self):
                    return reverse('books:delete', args=[self.id])

            class BookTable(StandardActionButtonModelTable):
                model = Book
                fields = ['title', 'isbn']

    """


class LookupModelTable(ActionButtonBlockMixin, ModelTableMixin, BaseDataTable):  # type: ignore[misc]
    """
    Specialized table for lookup/reference data with automatic field discovery.
    This is used by the :py:class:`wildewidgets.ModelViewSet` to display
    reference data like categories, statuses, or other lookup tables.

    This table is designed for displaying reference/lookup tables and
    automatically configures itself to:

    1. Show only direct model fields (no related fields)
    2. Left-align the ID column for better readability
    3. Support row actions via :py:class:`wildewidgets.ActionButtonBlockMixin`

    This table is ideal for admin interfaces or data management views for
    reference data like categories, statuses, or other lookup tables.

    Requirements:
        - Your model must implement ``get_absolute_url``, ``get_update_url`` and
          ``get_delete_url`` methods

    Note:
        If fields are not specified, the table automatically includes all
        non-relation fields from the model.

    Example:
        .. code-block:: python

            from django.db import models
            from wildewidgets.widgets.tables import LookupModelTable

            class Category(models.Model):
                name = models.CharField(max_length=100)
                description = models.TextField(blank=True, null=True)

                def get_absolute_url(self):
                    return f"/categories/{self.id}/"

                def get_update_url(self):
                    return f"/categories/{self.id}/edit/"

                def get_delete_url(self):
                    return f"/categories/{self.id}/delete/"

            class CategoryTable(LookupModelTable):
                model = Category

    Keyword Args:
        fields: A list of field names to include in the table. If not provided,
            defaults to all non-relation fields on the model.
        model: The Django model class to use for this table. If not provided,
            the :py:attr:`model` attribute must be set on the class.

    Raises:
        ImproperlyConfigured: If the model is not set as either a class attribute
            or provided during initialization.

    """

    actions: list[RowActionButton] = []  # noqa: RUF012

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop("fields", [])
        self.model = kwargs.get("model") or self.model
        if not self.model:
            msg = f"{self.__class__.__name__} requires a model to be set"
            raise ImproperlyConfigured(msg)
        if not fields and not self.fields:
            alignment = {}
            fields = []
            for field in self.model._meta.get_fields():
                if not isinstance(field, (RelatedField, ManyToManyRel)):
                    # Exclude any RelatedField
                    fields.append(field.name)
                    if field.name == "id":
                        alignment["id"] = "left"
            kwargs["fields"] = fields
            kwargs["alignment"] = alignment
        super().__init__(*args, **kwargs)
