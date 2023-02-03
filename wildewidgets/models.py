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


def model_verbose_name(model_class: Type[models.Model]) -> str:
    name = model_class._meta.verbose_name
    if not name[0].isupper():
        name = name.capitalize()
    return name


def model_verbose_name_plural(model_class: Type[models.Model]) -> str:
    name = model_class._meta.verbose_name_plural
    if not name[0].isupper():
        name = name.capitalize()
    return name


def model_name(model_class: Type[models.Model]) -> str:
    return model_class._meta.object_name


def model_logger_name(model_class: Type[models.Model]) -> str:
    return model_name(model_class).lower()


class ViewSetMixin(models.Model):
    """
    This mixin should be used on your :py:class:`django.db.models.Model` when you have
    assigned a :py:class:`wildewidgets.viewsets.ModelViewSet` to it.  It adds attributes
    and methods that ``ModelViewSet`` needs in order to function properly.

    Note:
        You can actually use this mixin even if you don't assign a viewset to
        your model.  The helper methods for autogenerating model forms,
        registering CRUD URLs, and generating properly capitalized model names and
        verbose names can be useful even outside the viewset context.

        In that case, you should consider setting the :py:attr:`create_url`
        attribute and overriding the :py:meth:`get_update_url`,
        :py:meth:`get_delete_url` methods.
    """
    # TODO: document customizing form classes
    # TODO: document adding methods to excludes

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
        """
        Return the name of our model class as a string.
        """
        return model_name(cls)

    @classmethod
    def model_logger_name(cls) -> str:
        """
        Return the name of our model class as a lowercased string that would be
        suitable for using in log messages, for instance.
        """
        return model_logger_name(cls)

    @classmethod
    def model_verbose_name(cls) -> str:
        """
        Return a properly capitalized ``verbose_name`` for our model.  If the first
        character of our ``verbose_name`` is already capitalized, return it verbatim,
        otherwise capitalize the first letter and return the result.
        """
        return model_verbose_name(cls)

    @classmethod
    def model_verbose_name_plural(cls) -> str:
        """
        Return a properly capitalized ``verbose_name_plural`` for our model.  If
        the first character of our ``verbose_name_plural`` is already
        capitalized, return it verbatim, otherwise capitalize the first letter
        and return the result.
        """
        return model_verbose_name_plural(cls)

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
