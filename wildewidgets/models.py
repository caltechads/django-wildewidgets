from typing import List, Optional, Type, TYPE_CHECKING

from django.forms import Form
from django.db import models
from django.urls import reverse

from wildewidgets.forms import (
    AbstractModelFormBuilder,
    AutoCrispyModelForm
)

if TYPE_CHECKING:
    from wildewidgets.viewsets import ModelViewSet


class ViewSetMixin(models.Model):

    #: If this model is served by a :py:class:`wildewidgets.viewsets.model.ModelViewSet`,
    #: that viewset will set this variable to itself, and we'll ask the viewset
    #: use the viewset to set our update, delete, and create urls
    viewset: "Optional[ModelViewSet]" = None
    #: Use this class when automatically constructing our form classes
    form_builder_class: AbstractModelFormBuilder = AutoCrispyModelForm
    #: The form we should use for this model when creating new instances
    create_form_class: Optional[Type[Form]] = None
    #: The form we should use for this model when updating existing instances
    update_form_class: Optional[Type[Form]] = None
    #: The form we should use for this model when deleting existing instances
    delete_form_class: Optional[Type[Form]] = None
    #: Exclude these fields from our auto constructed forms, in addition
    #: to the ones already excluded by our :py:attr:`form_builder_class`
    excludes: List[str] = []

    #: The url we should POST to to create new instances
    create_url: Optional[str] = None

    @classmethod
    def model_name(cls) -> str:
        return cls._meta.object_name

    @classmethod
    def model_logger_name(cls) -> str:
        return cls.model_name().lower()

    @classmethod
    def model_verbose_name(cls) -> str:
        name = cls._meta.verbose_name.capitalize()
        if not name[0].isupper():
            name = name.capitalize()
        return name

    @classmethod
    def model_verbose_name_plural(cls) -> str:
        name = cls._meta.verbose_name_plural.capitalize()
        if not name[0].isupper():
            name = name.capitalize()
        return name

    @classmethod
    def get_create_form_class(cls) -> Type[Form]:
        """
        Return a ``crispy_forms`` enabled :py:class:`django.forms.Form` for use
        in creating instances of this model.

        If :py:attr:`create_form_class` is not ``None``, return that, otherwise
        construct a :py:class:`django.forms.ModelForm` and return that instead.

        Returns:
            The create form.
        """
        if not cls.create_form_class:
            return cls.form_builder_class.factory(
                cls,
                cls.get_create_url(),
                excludes=cls.excludes
            )
        return cls.create_form_class

    @classmethod
    def get_create_url(cls) -> Optional[str]:
        """
        Return a URL suitable for POSTing to to create an instance of this
        model.  This defaults to the value of :py:attr:`create_url`.

        If :py:attr:`create_url` is `None`, try seeing if there's a viewset
        URL for us.

        Returns:
            The create URL.
        """
        if cls.viewset:
            return reverse(cls.viewset.get_url_name('create'))
        return cls.create_url

    def get_update_form_class(self) -> Type[Form]:
        """
        Return a ``crispy_forms`` enabled :py:class:`django.forms.Form` for use
        in updating this instance of this model.

        If :py:attr:`create_form_class` is not ``None``, return that, otherwise
        construct a :py:class:`django.forms.ModelForm` and return that instead.

        Returns:
            The update form.
        """
        if not self.update_form_class:
            return self.form_builder_class.factory(
                self.__class__,
                self.get_update_url(),
                excludes=self.excludes
            )
        return self.update_form_class

    def get_delete_form_class(self) -> Type[Form]:
        """
        Return a ``crispy_forms`` enabled :py:class:`django.forms.Form` for use
        in updating this instance of this model.

        If :py:attr:`create_form_class` is not ``None``, return that, otherwise
        construct a :py:class:`django.forms.ModelForm` and return that instead.

        Returns:
            The update form.
        """
        if not self.delete_form_class:
            return self.form_builder_class.factory(
                self.__class__,
                self.get_delete_url(),
                fields=["id"]
            )
        return self.delete_form_class

    def get_update_url(self) -> Optional[str]:
        """
        Return a URL suitable for POSTing to to update this instance of this
        model.

        Returns:
            The update URL for this instance.
        """
        if self.viewset:
            return reverse(self.viewset.get_url_name('update'), kwargs={'pk': self.pk})
        else:
            return None

    def get_absolute_url(self) -> Optional[str]:
        """
        Return the standard URL for viewing/editing this instance of this model.

        Returns:
            The update URL for this instance.
        """
        return self.get_update_url()

    def get_delete_url(self) -> Optional[str]:
        """
        Return a URL suitable for POSTing to to delete this instance of this
        model.

        Returns:
            The delete URL for this instance.
        """
        if self.viewset:
            return reverse(self.viewset.get_url_name('delete'), kwargs={'pk': self.pk})
        else:
            return None

    class Meta:
        abstract = True
