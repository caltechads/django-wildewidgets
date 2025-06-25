from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db import models
from django.urls import reverse

from wildewidgets.forms import AbstractModelFormBuilder, AutoCrispyModelForm

if TYPE_CHECKING:
    from django.forms import Form, ModelForm

    from wildewidgets.viewsets import ModelViewSet


def model_verbose_name(model_class: type[models.Model]) -> str:
    assert model_class._meta.verbose_name, (  # noqa: S101
        f"Model {model_class.__name__} does not have a verbose_name set. "
        "Please set the verbose_name attribute in the model's Meta class."
    )
    # Ensure the first letter is capitalized
    name = model_class._meta.verbose_name
    if not name[0].isupper():
        name = name.capitalize()
    return str(name)


def model_verbose_name_plural(model_class: type[models.Model]) -> str:
    assert model_class._meta.verbose_name_plural, (  # noqa: S101
        f"Model {model_class.__name__} does not have a verbose_name_plural set. "
        "Please set the verbose_name_plural attribute in the model's Meta class."
    )
    # Ensure the first letter is capitalized
    name = model_class._meta.verbose_name_plural
    if not name[0].isupper():
        name = name.capitalize()
    return str(name)


def model_name(model_class: type[models.Model]) -> str:
    return model_class._meta.object_name  # type: ignore[return-value]


def model_logger_name(model_class: type[models.Model]) -> str:
    return model_name(model_class).lower()


class ViewSetMixin(models.Model):
    """
    Used on your :py:class:`django.db.models.Model` when you have assigned a
    :py:class:`wildewidgets.viewsets.ModelViewSet` to it.  It adds attributes
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

    #: If this model is served by a
    #: :py:class:`wildewidgets.viewsets.model.ModelViewSet`, that viewset will
    #: set this variable to itself, and we'll ask the viewset use the viewset to
    #: set our update, delete, and create urls
    viewset: ModelViewSet | None = None
    #: Use this class when automatically constructing our form classes
    form_builder_class: type[AbstractModelFormBuilder] = AutoCrispyModelForm
    #: The form we should use for this model when creating new instances
    create_form_class: type[Form] | None = None
    #: The form we should use for this model when updating existing instances
    update_form_class: type[Form] | None = None
    #: The form we should use for this model when deleting existing instances
    delete_form_class: type[Form] | None = None
    #: Exclude these fields from our auto constructed forms, in addition
    #: to the ones already excluded by our :py:attr:`form_builder_class`
    excludes: list[str] = []  # noqa: RUF012

    #: The url we should POST to to create new instances
    create_url: str | None = None

    class Meta:
        abstract: bool = True

    def __str__(self) -> str:
        """
        Return a string representation of this model instance.

        This is used in the Django admin, and in other places where we need to
        display a human-readable representation of this model instance.

        Returns:
            A string representation of this model instance.

        """
        return f"{self.model_name()}({self.pk})"

    def get_absolute_url(self) -> str | None:
        """
        Return the standard URL for viewing/editing this instance of this model.

        Returns:
            The update URL for this instance.

        """
        return self.get_update_url()

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
    def get_create_form_class(cls) -> type[Form | ModelForm] | None:
        """
        Return a ``crispy_forms`` enabled :py:class:`django.forms.Form` for use
        in creating instances of this model.

        If :py:attr:`create_form_class` is not ``None``, return that, otherwise
        construct a :py:class:`django.forms.ModelForm` and return that instead.

        Returns:
            The create form, or ``None`` if no create form is available.

        """
        if not cls.create_form_class:
            create_url = cls.get_create_url()
            if not create_url:
                return None
            return cls.form_builder_class.factory(
                cls, create_url, excludes=cls.excludes
            )
        return cls.create_form_class

    @classmethod
    def get_create_url(cls) -> str | None:
        """
        Return a URL suitable for POSTing to to create an instance of this
        model.  This defaults to the value of :py:attr:`create_url`.

        If :py:attr:`create_url` is `None`, try seeing if there's a viewset
        URL for us.

        Returns:
            The create URL.

        """
        if cls.viewset:
            return reverse(cls.viewset.get_url_name("create"))
        return cls.create_url

    def get_update_form_class(self) -> type[Form | ModelForm] | None:
        """
        Return a ``crispy_forms`` enabled :py:class:`django.forms.Form` for use
        in updating this instance of this model.

        If :py:attr:`create_form_class` is not ``None``, return that, otherwise
        construct a :py:class:`django.forms.ModelForm` and return that instead.

        Returns:
            The update form, or ``None`` if no update form is available.

        """
        if not self.update_form_class and self.viewset:
            update_url = self.get_update_url()
            if not update_url:
                return None
            return self.form_builder_class.factory(
                self.__class__, update_url, excludes=self.excludes
            )
        return self.update_form_class

    def get_delete_form_class(self) -> type[Form | ModelForm] | None:
        """
        Return a ``crispy_forms`` enabled :py:class:`django.forms.Form` for use
        in updating this instance of this model.

        If :py:attr:`create_form_class` is not ``None``, return that, otherwise
        construct a :py:class:`django.forms.ModelForm` and return that instead.

        Returns:
            The update form.

        """
        if not self.delete_form_class and self.viewset:
            delete_url = self.get_delete_url()
            if not delete_url:
                return None
            return self.form_builder_class.factory(
                self.__class__, delete_url, fields=["id"]
            )
        return self.delete_form_class

    def get_update_url(self) -> str | None:
        """
        Return a URL suitable for POSTing to to update this instance of this
        model.

        Returns:
            The update URL for this instance.

        """
        if self.viewset:
            return reverse(self.viewset.get_url_name("update"), kwargs={"pk": self.pk})
        return None

    def get_delete_url(self) -> str | None:
        """
        Return a URL suitable for POSTing to to delete this instance of this
        model.

        Returns:
            The delete URL for this instance.

        """
        if self.viewset:
            return reverse(self.viewset.get_url_name("delete"), kwargs={"pk": self.pk})
        return None
