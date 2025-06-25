from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Field, Fieldset, Layout, Submit
from django.core.exceptions import ImproperlyConfigured
from django.db.models.fields import (
    AutoFieldMixin,
    BooleanField,
    DateField,
    DateTimeField,
    TextField,
)
from django.db.models.fields import Field as DjangoField
from django.db.models.fields.related import (
    ManyToManyField,
    ManyToManyRel,
    RelatedField,
)
from django.forms import (
    CheckboxInput,
    CheckboxSelectMultiple,
    Form,
    ModelForm,
    MultipleChoiceField,
    Textarea,
    modelform_factory,
)

if TYPE_CHECKING:
    from django.db.models import Model
    from django.forms.widgets import Widget as DjangoWidget

try:
    from django_extensions.db.fields import (
        AutoSlugField,
        CreationDateTimeField,
        ModificationDateTimeField,
    )

    has_django_extensions = True
except ImportError:
    has_django_extensions = False


class AbstractModelFormBuilder:
    """
    An abstract base class for building ModelForms with customized configurations.

    This class serves as a foundation for creating ModelForm factories that can
    automatically generate well-configured forms for Django models. It provides
    a factory method pattern for consistent form creation.

    Subclasses should implement the factory method to provide specific form
    generation logic tailored to their needs.
    """

    @classmethod
    def factory(  # type: ignore[empty-body]
        cls,
        model_class: type[Model],
        form_action: str,
        fields: list[str] | None = None,
        excludes: list[str] | None = None,
    ) -> type[ModelForm]:
        """
        Construct a form class for the specified model class.

        This abstract method should be implemented by subclasses to provide
        custom form building logic.

        Args:
            model_class: The model class for which to build a form
            form_action: The URL to which the form will be submitted
            fields: Optional list of fields to include in the form
            excludes: Optional list of fields to exclude from the form

        Returns:
            A configured ModelForm class

        Raises:
            NotImplementedError: If not implemented by a subclass

        """
        # Implementation required by subclasses


class AbstractRelatedModelFormBuilder:
    """
    An abstract base class for building forms that manage related model fields.

    This class provides a foundation for creating forms that specifically handle
    relationships between models, such as ManyToMany fields. It simplifies the
    process of building forms for managing these relationships.

    Subclasses should implement the factory method to provide specific form
    generation logic for related fields.
    """

    @classmethod
    def factory(  # type: ignore[empty-body]
        cls, model_class: type[Model], field_name: str, form_action: str
    ) -> type[ModelForm]:
        """
        Construct a form class for managing a related field on a model.

        This abstract method should be implemented by subclasses to provide
        custom form building logic for related fields.

        Args:
            model_class: The model class containing the related field
            field_name: The name of the related field to manage
            form_action: The URL to which the form will be submitted

        Returns:
            A configured ModelForm class

        Raises:
            NotImplementedError: If not implemented by a subclass

        """
        # Implementation required by subclasses


class AutoCrispyModelForm(AbstractModelFormBuilder, ModelForm):
    """
    A ModelForm with automatic crispy-forms styling and intelligent field
    configuration.

    This class provides a powerful way to create forms that:

    1. Automatically exclude fields that shouldn't be edited by users
    2. Apply appropriate widgets based on field types
    3. Style the form using crispy-forms with Bootstrap
    4. Handle form submission with proper action URLs

    The form intelligently handles common field types:

    - Auto-incrementing fields are excluded
    - Auto-timestamp fields are excluded
    - Text fields use textareas with appropriate dimensions
    - Boolean fields use toggle switches

    Example:
        .. code-block:: python

            from django.db import models
            from django.forms import ModelForm
            from django.shortcuts import redirect, render
            from django.urls import reverse_lazy
            from django.views.generic import CreateView
            from wildewidgets.forms import AutoCrispyModelForm

            class Book(models.Model):
                title = models.CharField(max_length=200)
                author = models.CharField(max_length=100)
                published_date = models.DateField()
                created_at = models.DateTimeField(auto_now_add=True)

                class Meta:
                    verbose_name = "book"
                    verbose_name_plural = "books"


            # Create a form class for the Book model
            BookForm = AutoCrispyModelForm.factory(
                Book,
                reverse('book-create'),
                excludes=['created_at']
            )

            class BookCreateView(CreateView):
                form_class = BookForm
                template_name = 'book_form.html'
                success_url = reverse_lazy('book-list')

    """

    #: The URL to which we will post this form
    form_action: str
    #: How much margin we should put vertically between inputs
    vertical_spacing: str = "mb-2"

    @classmethod
    def factory(
        cls,
        model_class: type[Model],
        form_action: str,
        fields: list[str] | None = None,
        excludes: list[str] | None = None,
    ) -> type[ModelForm]:
        """
        Construct a form class for the :py:class:`Model` subclass ``model_class``
        and return it.

        Exclude these kinds of fields from the form:

        * :py:class:`django.db.fields.AutoField`
        * :py:class:`django.db.fields.BigAutoField`
        * :py:class:`django.db.fields.SmallAutoField`
        * :py:class:`django.db.fields.DateField` with ``auto_now == True``
        * :py:class:`django.db.fields.DateTimeField` with ``auto_now == True``

        If you use ``django_extensions``, we also exclude these fields from the form:

        * :py:class:`django_extensions.db.fields.CreationDateTimeField`
        * :py:class:`django_extensions.db.fields.ModificationDateTimeField`
        * :py:class:`django_extensions.db.fields.AutoSlugField`

        Assign widgets for some common use cases:

        * Use :py:class:`django.forms.Textarea` for
          :py:class:`django.db.fields.TextField` fields
        * Give all :py:class:`django.db.fields.BooleanField` fields Bootstrap 5
          Switch styling (See `Bootstrap 5 Checks and Radios
          <https://getbootstrap.com/docs/5.2/forms/checks-radios/#switches>`_)

        Note:
            Specify either ``fields`` or ``excludes``, but not both.

        Args:
            model_class: the model class for which to build a form
            form_action: the URL to which to post our form

        Keyword Args:
            fields: include these fields in the form.
                If ``None``, include all fields except those excluded by type.
                If specified, only include these fields in the form.
                Note: Specify either ``fields`` or ``excludes``, but not both.
            excludes: exclude fields named in this list in addition to ones
                excluded by type

        Returns:
            A configured form class.

        """
        if fields and excludes:
            msg = 'Specify either "fields" or "excludes" but not both'
            raise ImproperlyConfigured(msg)
        _excludes = set(excludes) if excludes else set()
        widgets: dict[str, DjangoWidget] = {}
        excluded_types = [
            # All the auto fields are derived from this mixin.  Exclude such
            # fields because humans shouldn't muck with them.
            AutoFieldMixin,
            # Skip related fields -- no easy way to pick them
            RelatedField,
        ]
        if has_django_extensions:
            excluded_types.extend(
                [
                    CreationDateTimeField,
                    ModificationDateTimeField,
                    AutoSlugField,
                ]
            )
        for field in model_class._meta.get_fields():
            if not fields and isinstance(field, tuple(excluded_types)):
                # Exclude any field that should not be user editable
                _excludes.add(field.name)
            if (
                not fields
                and isinstance(field, (DateTimeField, DateField))
                and field.auto_now
            ):
                # Exclude any DateField or DateTimeField that sets its time
                # automatically
                _excludes.add(field.name)
            elif isinstance(field, TextField):
                # Always make TextFields use Textareas
                widgets[field.name] = Textarea(attrs={"cols": 50, "rows": 3})
            elif isinstance(field, BooleanField):
                # Make our BooleanFields be switches.  This also requires
                # some work in our :py:meth:`build_fieldset`
                widgets[field.name] = CheckboxInput(attrs={"role": "switch"})

        form = modelform_factory(
            model_class,
            form=cls,
            fields=fields,
            exclude=list(_excludes),
            widgets=widgets,  # type: ignore[arg-type]
        )
        form.form_action = form_action
        return form

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-lg-3"
        self.helper.field_class = "col"
        self.helper.form_method = "post"
        self.helper.form_action = self.form_action
        self.helper.layout = Layout(
            self.build_fieldset(),
            ButtonHolder(
                Submit("submit", "Save", css_class="btn btn-primary"),
                css_class="d-flex flex-row justify-content-end w-100 mt-3",
            ),
        )

    def build_fieldset(self) -> Fieldset:
        """
        Build a :py:class:`Fieldset` with all our form fields properly
        configured, and return it.
        """
        fields = [""]
        for name, field in self.fields.items():
            if isinstance(field.widget, CheckboxInput):
                # Make our checkboxes look like Bootstrap 5 switches
                fields.append(
                    Field(
                        name,
                        wrapper_class="form-check form-switch",
                        css_class=self.vertical_spacing,
                    )
                )
            else:
                fields.append(Field(name, css_class=self.vertical_spacing))
        return Fieldset(*fields)


class AbstractRelatedFieldForm(Form):
    """
    An abstract base class for forms that manage a single related field on a model.

    This class provides the foundation for creating forms that handle specific
    relationship fields on models. It handles the setup, validation, and saving
    of changes to a related field (like a ForeignKey or ManyToMany field).

    The form is initialized with a model instance and a field name, and it
    provides methods for generating appropriate form fields and saving changes.

    Example:
        .. code-block:: python

            from django import forms
            from django.db.models import Model
            from django.forms import ModelChoiceField
            from wildewidgets.forms import AbstractRelatedFieldForm
            from myapp.models import Category, Book

            class CategoryForm(forms.ModelForm):
                class Meta:
                    model = Category
                    fields = ['name']

            class Book(Model):
                title = models.CharField(max_length=200)
                category = models.ForeignKey(Category, on_delete=models.CASCADE)

            # Example subclass for managing a ForeignKey relationship
            class BookCategoryForm(AbstractRelatedFieldForm):
                field_name = 'category'  # The ForeignKey field on the Book model

                def get_fields(self):
                    fields = super().get_fields()
                    fields[self.field_name] = ModelChoiceField(
                        queryset=Category.objects.all(),
                        initial=getattr(self.instance, self.field_name)
                    )
                    return fields

    Args:
        instance: The model instance whose related field we want to manage
        *args: Variable length argument list passed to parent

    Keyword Args:
        field_name: The name of the related field to manage. This must be provided
            either as a constructor keyword argument or as a class attribute.
        form_action: The URL to which the form will be submitted. If not provided,
            it will default to the URL of the view that uses this form as its
            `form_class`.
        **kwargs: Arbitrary keyword arguments passed to the parent Form class

    Raises:
        ImproperlyConfigured: If `field_name` is not provided
        TypeError: If the specified field is not a related field (ForeignKey,
            ManyToManyField, etc.)

    """

    #: The name of the  :py:class:`django.db.models.ManyToManyField` we want to manage
    field_name: str | None = None
    #: If not provided, this will be set to the URL of the view that uses this form
    #: as its form_class.
    form_action: str | None = None

    def __init__(
        self,
        instance: Model,
        *args,
        field_name: str | None = None,
        form_action: str | None = None,
        **kwargs,
    ):
        #: The instance whose :py:class:`django.db.models.ManyToManyField` we
        #: want to manage
        self.instance = instance
        self.field_name = field_name if field_name else self.field_name
        if not self.field_name:
            msg = (
                'You must provide "field_name" as either a constructor keyword '
                "argument or as a class attribute"
            )
            raise ImproperlyConfigured(msg)
        self.form_action = form_action if form_action else self.form_action
        super().__init__(*args, **kwargs)
        #: The field instance for our related field
        self.field = instance._meta.get_field(self.field_name)
        if not isinstance(self.field, RelatedField):
            msg = (
                f"{instance._meta.object_name}.{self.field_name} is not a related "
                f"field. It is instead a {self.field.__class__.__name__}."
            )
            raise TypeError(msg)
        #: The related model for the related field
        self.related_model = self.field.related_model
        self.pk_field_name = cast("DjangoField", instance._meta.pk).name
        self.fields = self.get_fields()

        self.helper = FormHelper()
        self.helper.form_class = "form"
        self.helper.form_method = "post"
        self.helper.form_show_labels = False
        self.helper.form_action = self.form_action
        self.helper.layout = self.get_fieldset()

    def get_fields(self) -> dict[str, Any]:
        return {}

    def get_fieldset(self) -> Fieldset:
        return Layout(
            Fieldset("", Field(self.field_name, id=self.field_name)),
            ButtonHolder(
                Submit("submit", "Update", css_class="btn btn-primary"),
                css_class="d-flex flex-row justify-content-end button-holder",
            ),
        )

    def save(self) -> Model:
        setattr(self.instance, self.field_name, self.cleaned_data[self.field_name])  # type: ignore[arg-type, index]
        return self.instance


class ToggleableManyToManyFieldForm(AbstractRelatedFieldForm):
    """
    A form for managing many-to-many relationships using a toggleable interface.

    This form presents all available related objects as toggle switches, allowing
    users to easily add or remove relationships. It's specifically designed for
    many-to-many fields and provides an intuitive interface for managing these
    relationships.

    The form automatically:

    1. Retrieves all possible related objects
    2. Shows which ones are currently related
    3. Provides a toggle switch for each option
    4. Handles saving the updated relationships

    Example:
        .. code-block:: python

            from django import forms
            from django.db.models import Model
            from django.forms import MultipleChoiceField, CheckboxSelectMultiple
            from wildewidgets.forms import ToggleableManyToManyFieldForm


            class Author(Model):
                name = models.CharField(max_length=100)

            class Book(Model):
                title = models.CharField(max_length=200)
                authors = models.ManyToManyField(Author)

            class AuthorsForm(ToggleableManyToManyFieldForm):
                field_name = 'authors'  # The ManyToManyField on the Book model

            class BookAuthorsView(FormView):
                form_class = AuthorsForm
                success_url = '/books/'
                template_name = "book_authors.html"

                def get_form_kwargs(self):
                    kwargs = super().get_form_kwargs()
                    kwargs['instance'] = Book.objects.get(pk=self.kwargs['pk'])
                    kwargs['field_name'] = 'authors'
                    return kwargs

    Args:
        *args: Variable length argument list passed to parent

    Keyword Args:
        **kwargs: Arbitrary keyword arguments passed to parent

    Raises:
        TypeError: If the specified field is not a ManyToManyField or
                    ManyToManyRel (reverse relation)


    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not isinstance(self.field, (ManyToManyField, ManyToManyRel)):
            msg = (
                f"{self.instance._meta.object_name}.{self.field_name} is not "
                "a ManyToManyField or many-to-many reverse relation.  Instead, it is a "
                f"{self.field.__class__.__name__}"
            )
            raise TypeError(msg)

    def get_fields(self) -> dict[str, Any]:
        """
        Create a MultipleChoiceField with all possible related objects.

        This method:

        1. Gets all possible related objects as choices
        2. Determines which ones are currently selected
        3. Creates a MultipleChoiceField with checkboxes for each option

        Returns:
            dict: Dictionary containing the field configuration for the form

        """
        fields = super().get_fields()
        choices = [(r.pk, str(r)) for r in self.related_model.objects.all()]
        related_pk_name = cast("DjangoField", self.related_model._meta.pk).name
        initial = list(
            getattr(self.instance, self.field_name).values_list(  # type: ignore[arg-type]
                related_pk_name, flat=True
            )
        )
        fields[self.field_name] = MultipleChoiceField(  # type: ignore[index]
            choices=choices,
            initial=initial,
            required=False,
            widget=CheckboxSelectMultiple(attrs={"class": "form-control"}),
        )
        return fields

    def get_fieldset(self) -> Fieldset:
        """
        Create a fieldset with toggle switches for the many-to-many options.

        This method customizes the field display to use Bootstrap 5 toggle switches
        with a reverse orientation, making them more visually appealing.

        Returns:
            Layout: A crispy_forms Layout object with the fieldset and submit button

        """
        return Layout(
            Fieldset(
                "",
                Field(
                    self.field_name,
                    id=self.field_name,
                    wrapper_class="form-check form-switch form-check-reverse",
                ),
            ),
            ButtonHolder(
                Submit("submit", "Update", css_class="btn btn-primary"),
                css_class="d-flex flex-row justify-content-end button-holder",
            ),
        )

    def save(self) -> Model:
        """
        Save the updated many-to-many relationships.

        This method takes the selected values from the form and updates the
        many-to-many relationship accordingly, adding and removing relationships
        as needed.

        Returns:
            Model: The updated model instance

        """
        getattr(self.instance, self.field_name).set(self.cleaned_data[self.field_name])  # type: ignore[arg-type, index]
        return self.instance
