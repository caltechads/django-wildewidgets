from typing import List, Type

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Fieldset, ButtonHolder
from django.forms import ModelForm, Textarea, CheckboxInput, modelform_factory
from django.db.models import Model
from django.db.models.fields import (
    AutoFieldMixin,
    BooleanField,
    DateField,
    DateTimeField,
    TextField,
)
from django.db.models.fields.related import RelatedField
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
