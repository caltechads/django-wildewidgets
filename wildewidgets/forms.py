from typing import Any, Dict, List, Optional, Type

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Fieldset, ButtonHolder
from django.forms import (
    CheckboxInput,
    CheckboxSelectMultiple,
    Form,
    HiddenInput,
    ModelForm,
    MultipleChoiceField,
    Textarea,
    modelform_factory
)
from django.db.models import Model
from django.db.models.fields import (
    AutoFieldMixin,
    BooleanField,
    DateField,
    DateTimeField,
    TextField,
)
from django.db.models.fields.related import (
    RelatedField,
    ManyToManyField,
    ManyToManyRel,
    ManyToOneRel
)
try:
    from django_extensions.db.fields import (
        CreationDateTimeField,
        ModificationDateTimeField,
        AutoSlugField
    )
    has_django_extensions = True
except ImportError:
    has_django_extensions = False


class AbstractModelFormBuilder:
    """
    A base class for a :py:class:`django.forms.ModelForm` builder, which
    automatically builds a decent ``ModelForm`` based on a
    :py:class:`django.db.models.Model`.
    """

    @classmethod
    def factory(
        cls,
        model_class: Type[Model],
        form_action: str,
        fields: List[str] = None,
        excludes: List[str] = None,
    ) -> "Type[ModelForm]":
        """
        Construct a form class for the :py:class:`Model` subclass ``model_class``
        and return it.


        Args:
            model_class: the model class for which to build a form
            form_class_name: the name to use for the form class
            form_action: the URL to which to post our form

        Keyword Args:
            excludes: exclude fields named in this list in addition

        Returns:
            A configured form class.
        """


class AbstractRelatedModelFormBuilder:
    """
    A base class for a formbuilder for building a form which allows users to
    manage multi-select ManyToManycontains only a
    :py:class:`django.forms.CheckboxSelectMultiple` widget that allows the user
    to manage a :py:class:`django.db.models.ManyToManyField` from a model to a
    lookup table and vice-versa.
    """

    @classmethod
    def factory(
        cls,
        model_class: Type[Model],
        field_name: str,
        form_action: str
    ) -> "Type[ModelForm]":
        """
        Construct a form class for the :py:class:`Model` subclass ``model_class``
        and return it.


        Args:
            model_class: the model class for which to build a form
            form_class_name: the name to use for the form class
            form_action: the URL to which to post our form

        Keyword Args:
            excludes: exclude fields named in this list in addition

        Returns:
            A configured form class.
        """


class AutoCrispyModelForm(AbstractModelFormBuilder, ModelForm):
    """
    This is a :py:class:`ModelForm` styled with ``django-crispy-forms` widgets
    that automatically configures itself to look like we want based on how our
    ``Meta`` class settings.

    * Set this to be a ``POST`` form
    * Set our form action to :py:attr:`form_action`
    * Style our inputs with Boostrap styling
    * Add a submit button
    """

    #: The URL to which we will post this form
    form_action: str
    #: How much margin we should put vertically between inputs
    vertical_spacing: str = 'mb-2'

    @classmethod
    def factory(
        cls,
        model_class: Type[Model],
        form_action: str,
        fields: List[str] = None,
        excludes: List[str] = None,
    ) -> "Type[AutoCrispyModelForm]":
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

        * Use :py:class:`django.forms.Textarea` for :py:class:`django.db.fields.TextField` fields
        * Give all :py:class:`dhango.db.fields.BooleanField` fields Bootstrap 5 Switch styling
          (See `Bootstrap 5 Checks and Radios <https://getbootstrap.com/docs/5.2/forms/checks-radios/#switches>`_)

        Note:
            Specify either ``fields`` or ``excludes``, but not both.

        Args:
            model_class: the model class for which to build a form
            form_action: the URL to which to post our form

        Keyword Args:
            fields: include these fields in the form.
            excludes: exclude fields named in this list in addition to ones excluded by type

        Returns:
            A configured form class.
        """
        if fields and excludes:
            raise ValueError('Specify either "fields" or "excludes" but not both')
        excludes = excludes if excludes else []
        excludes = set(excludes)
        widgets = {}
        excluded_types = [
            # All the auto fields are derived from this mixin.  Exclude such
            # fields because humans shouldn't muck with them.
            AutoFieldMixin,
            # Skip related fields -- no easy way to pick them
            RelatedField,
        ]
        if has_django_extensions:
            excluded_types.extend([
                CreationDateTimeField,
                ModificationDateTimeField,
                AutoSlugField,
            ])
        for field in model_class._meta.get_fields():
            if not fields and isinstance(field, tuple(excluded_types)):
                # Exclude any field that should not be user editable
                excludes.add(field.name)
            if not fields and isinstance(field, (DateTimeField, DateField)) and field.auto_now:
                # Exclude any DateField or DateTimeField that sets its time automatically
                excludes.add(field.name)
            elif isinstance(field, TextField):
                # Always make TextFields use Textareas
                widgets[field.name] = Textarea(attrs={'cols': 50, 'rows': 3})
            elif isinstance(field, BooleanField):
                # Make our BooleanFields be switches.  This also requires
                # some work in our :py:meth:`build_fieldset`
                widgets[field.name] = CheckboxInput(attrs={'role': 'switch'})

        form = modelform_factory(
            model_class,
            form=cls,
            fields=fields,
            exclude=list(excludes),
            widgets=widgets
        )
        form.form_action = form_action
        return form

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col'
        self.helper.form_method = 'post'
        self.helper.form_action = self.form_action
        self.helper.layout = Layout(
            self.build_fieldset(),
            ButtonHolder(
                Submit('submit', 'Save', css_class='btn btn-primary'),
                css_class='d-flex flex-row justify-content-end w-100 mt-3'
            )
        )

    def build_fieldset(self) -> Fieldset:
        """
        Build a :py:class:`Fieldset` with all our form fields properly
        configured, and return it.
        """
        fields = ['']
        for name, field in self.fields.items():
            if isinstance(field.widget, CheckboxInput):
                # Make our checkboxes look like Bootstrap 5 switches
                fields.append(
                    Field(
                        name,
                        wrapper_class='form-check form-switch',
                        css_class=self.vertical_spacing
                    )
                )
            else:
                fields.append(Field(name, css_class=self.vertical_spacing))
        return Fieldset(*fields)


class AbstractRelatedFieldForm(Form):
    """
    This abstract class is the basis for creating forms that manage a single
    related field on a model.
    """

    #: The name of the  :py:class:`django.db.models.ManyToManyField` we want to manage
    field_name: Optional[str] = None
    form_action: Optional[str] = None

    def __init__(
        self,
        instance: Model,
        *args,
        field_name: str = None,
        form_action: str = None,
        **kwargs
    ):
        #: The instance whose :py:class:`django.db.models.ManyToManyField` we want to manage
        self.instance = instance
        self.field_name = field_name if field_name else self.field_name
        self.form_action = form_action if form_action else self.form_action
        if self.field_name is None:
            raise ValueError(
                'You must provide "field_name" as either a constructor keyword argument '
                'or as a class attribute'
            )
        super().__init__(*args, **kwargs)
        #: The field instance for our related field
        self.field = instance._meta.get_field(self.field_name)
        if not isinstance(self.field, RelatedField):
            raise ValueError(
                f'{instance._meta.object_name}.{self.field_name} is not a related field. '
                f'It is instead a {self.field.__class__.__name__}.'
            )
        #: The related model for the related field
        self.related_model = self.field.related_model
        self.pk_field_name = instance._meta.pk.name
        self.fields = self.get_fields()

        self.helper = FormHelper()
        self.helper.form_class = 'form'
        self.helper.form_method = 'post'
        self.helper.form_show_labels = False
        self.helper.form_action = self.form_action
        self.helper.layout = self.get_fieldset()

    def get_fields(self) -> Dict[str, Any]:
        return {}

    def get_fieldset(self) -> Fieldset:
        return Layout(
            Fieldset(
                '',
                Field(self.field_name, id=self.field_name)
            ),
            ButtonHolder(
                Submit('submit', 'Update', css_class='btn btn-primary'),
                css_class='d-flex flex-row justify-content-end button-holder'
            )
        )

    def save(self) -> Model:
        setattr(self.instance, self.cleaned_data[self.field_name])
        return self.instance


class ToggleableManyToManyFieldForm(AbstractRelatedFieldForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not isinstance(self.field, (ManyToManyField, ManyToManyRel)):
            raise ValueError(
                f'{self.instance._meta.object_name}.{self.field_name} is not a ManyToManyField or many-to-many reverse '
                f'relation.  Instead, it is a {self.field.__class__.__name__}'
            )

    def get_fields(self) -> Dict[str, Any]:
        fields = super().get_fields()
        choices = [(r.pk, str(r)) for r in self.related_model.objects.all()]
        related_pk_name = self.related_model._meta.pk.name
        initial = list(
            getattr(self.instance, self.field_name)
            .values_list(related_pk_name, flat=True)
        )
        fields[self.field_name] = MultipleChoiceField(
            choices=choices,
            initial=initial,
            required=False,
            widget=CheckboxSelectMultiple(attrs={"class": "form-control"})
        )
        return fields

    def get_fieldset(self) -> Fieldset:
        return Layout(
            Fieldset(
                '',
                Field(
                    self.field_name,
                    id=self.field_name,
                    wrapper_class='form-check form-switch form-check-reverse',
                ),
            ),
            ButtonHolder(
                Submit('submit', 'Update', css_class='btn btn-primary'),
                css_class='d-flex flex-row justify-content-end button-holder'
            )
        )

    def save(self) -> Model:
        getattr(self.instance, self.field_name).set(self.cleaned_data[self.field_name])
        return self.instance
