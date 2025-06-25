from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from django.urls import URLPattern, path, reverse

from ..forms import ToggleableManyToManyFieldForm
from .base import Block
from .structure import CardWidget, HorizontalLayoutBlock

if TYPE_CHECKING:
    from django.db.models import Model
    from django.forms import Form


class LabelBlock(Block):
    """
    A ``<label>``

    Args:
        text: the text for the label

    Keyword Args:
        bold: if ``True``, make the label text be bold
        color: the bootstrap/tabler color to assign to the label
        for_input: the CSS id of the input this describes

    """

    tag: str = "label"

    #: If ``True``, make the label text be bold
    bold: bool = True
    #: The CSS id of the input this describes
    for_input: str | None = None

    def __init__(
        self,
        text: str,
        for_input: str | None = None,
        bold: bool | None = None,
        color: str = "secondary",  # noqa: ARG002
        **kwargs: Any,
    ) -> None:
        self.bold = bold if bold is not None else self.bold
        self.for_input = for_input if for_input is not None else self.for_input
        super().__init__(text, **kwargs)
        if self.for_input:
            self._attributes["for"] = self.for_input
        if self.bold:
            self.add_class("fw-bold")


class InputBlock(Block):
    """
    A block for rendering a simple ``<input>`` element.

    Example:
        .. code-block:: python

            from wildewidgets import InputBlock

            # A simple text input
            block = InputBlock(input_type='text', input_name='my-input', value='Hello')

    Keyword Args:
        input_type: the value of the ``type`` attribute
        input_name: the value of the ``name`` attribute
        value: the value of the ``value`` attribute

    """

    empty: bool = True
    tag: str = "input"

    input_type: str | None = None
    input_name: str | None = None
    value: str | None = None

    def __init__(
        self,
        input_type: str | None = None,
        input_name: str | None = None,
        value: str | None = None,
        **kwargs: Any,
    ) -> None:
        self.input_type = input_type if input_type else self.input_type
        self.input_name = input_name if input_name else self.input_name
        self.value = value if value else self.value
        super().__init__(**kwargs)
        if self.input_type is not None:
            self._attributes["type"] = self.input_type
        if self.input_name is not None:
            self._attributes["name"] = self.input_name
        if self.value is not None:
            self._attributes["value"] = self.value


class BaseCheckboxInputBlock(InputBlock):
    """
    A block for rendering a bare ``<input type="checkbox">`` element.

    Example:

        .. code-block:: python

            from wildewidgets import BaseCheckboxInputBlock

            block_unchecked = BaseCheckboxInputBlock(input_name='my-checkbox', value=1)
            block_checked = BaseCheckboxInputBlock(
                input_name='my-checkbox',
                value=1,
                checked=True
            )

    Keyword Args:
        checked: if ``True``, render the checkbox as checked

    """

    input_type: str = "checkbox"

    def __init__(
        self,
        checked: bool = False,
        **kwargs: Any,
    ) -> None:
        self.checked = checked
        super().__init__(**kwargs)
        if not self.input_name:
            msg = "input_name"
            raise self.RequiredAttrOrKwarg(msg)
        if not self.value:
            msg = "value"
            raise self.RequiredAttrOrKwarg(msg)
        if self.checked:
            self._attributes["checked"] = ""


class CheckboxInputBlock(Block):
    """
    A block for rendering a ``<input type="checkbox">`` element with a label as a
    `Boostrap 5 check <https://getbootstrap.com/docs/5.2/forms/checks-radios/#checks>`_.

    Example:

        .. code-block:: python

            from wildewidgets import CheckboxInputBlock

            block = CheckboxInputBlock(
                label_text='My Checkbox',
                name='my-checkbox',
                value=1
            )

    Keyword Args:
        label_text: the text to use for the label
        bold: if ``True``, make the label text be bold
        input_name: the value of the ``name`` attribute
        value: the value of the ``value`` attribute
        checked: if ``True``, render the checkbox as checked

    """

    #: The value of the ``name`` attribute on the checkbox
    input_name: str | None = None
    #: The value of the ``value`` attribute on the checkbox
    value: str | None = None
    #: The text to use for the label for the checkbox
    label_text: str | None = None
    #: if ``True``, make the label text be bold
    bold: bool = True

    def __init__(
        self,
        label_text: str | None = None,
        bold: bool | None = None,
        input_name: str | None = None,
        value: str | None = None,
        checked: bool = False,
        **kwargs: Any,
    ) -> None:
        self.label_text = label_text if label_text else self.label_text
        self.input_name = input_name if input_name else self.input_name
        self.bold = bold if bold is not None else self.bold
        self.value = value if value else self.value
        if not self.label_text:
            msg = "label_text"
            raise self.RequiredAttrOrKwarg(msg)
        if not self.input_name:
            msg = "input_name"
            raise self.RequiredAttrOrKwarg(msg)
        if not self.value:
            msg = "value"
            raise self.RequiredAttrOrKwarg(msg)
        self.input_css_id = kwargs.pop(
            "css_id", f"checkbox-{self.input_name}-{self.value}"
        )
        self.checked = checked
        super().__init__(**kwargs)
        self.add_class("form-check")
        self.add_block(
            BaseCheckboxInputBlock(
                input_name=self.input_name,
                value=self.value,
                css_id=self.input_css_id,
                checked=self.checked,
                css_class="form-check-input",
            )
        )
        self.add_block(
            LabelBlock(
                text=self.label_text,
                bold=self.bold,
                for_input=self.input_css_id,
                css_class="form-check-label",
            )
        )


class ToggleSwitchInputBlock(CheckboxInputBlock):
    """
    A block for rendering a ``<input type="checkbox">`` element with a label as
    a `Bootstrap 5 switch <https://getbootstrap.com/docs/5.0/forms/checks-radios/#switches>`_.

    Example:
        .. code-block:: python

            from wildewidgets import ToggleSwitchInputBlock

            block = ToggleSwitchInputBlock(
                label_text='My Checkbox',
                name='my-checkbox',
                value=1
            )

    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.add_class("form-switch")


class HiddenInputBlock(InputBlock):
    """
    A block for rendering a ``<input type="hidden">``.

    Example:

        .. code-block:: python

            from wildewidgets import HiddenInputBlock

            block = HiddenInputBlock(name='my-checkbox', value=1)

    """

    input_type: str = "hidden"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if not self.input_name:
            msg = "input_name"
            raise self.RequiredAttrOrKwarg(msg)
        if not self.value:
            msg = "value"
            raise self.RequiredAttrOrKwarg(msg)


class CrispyFormWidget(Block):
    """
    A widget that displays a Crispy Form widget.  This is specifically a Crispy
    Form widget because it uses the ``{% crispy %}`` template tag to render the
    form.

    Note:
        If the form is present in the template context already, (because your
        view inserted it for you) you don't need to supply the ``form`` keyword
        argument -- ``CrispyFormWidget`` will pick it up automatically.

    Example:
        .. code-block:: python

            from wildewidgets import CrispyFormWidget
            from myapp.forms import MyCrispyForm

            block = CrispyFormWidget(form=MyCrispyForm())

    Args:
        *blocks: Any blocks to add to this widget.  These will be rendered in the
            order they are provided.

    Keyword Args:
        form: A crispy form to display. If none is specified, it will be assumed
            that ``form`` is specified elsewhere in the context.
        **kwargs: Any additional keyword arguments to pass to the parent class.

    """

    #: The Django template to use to render this widget.
    template_name: str = "wildewidgets/crispy_form_widget.html"
    #: The name of this block.
    block: str = "wildewidgets-crispy-form-widget"

    def __init__(self, *blocks: Any, form: Form | None = None, **kwargs: Any) -> None:
        super().__init__(*blocks, **kwargs)
        self.form = form

    def get_context_data(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        kwargs = super().get_context_data(*args, **kwargs)
        if self.form:
            kwargs["form"] = self.form
        return kwargs


class ToggleableManyToManyFieldBlock(CardWidget):
    """
    A block that allows you to manage a many-to-many relationship between a
    model and a related model as a list of toggleable items.

    This widget displays all available related objects as toggle switches,
    with currently selected items checked. It provides interactive features
    including:

    - A toggle to hide/show unselected items
    - A search box to filter items by name

    This is most appropriate for relationships between a model and a
    lookup table (e.g., categories, tags, classifiers, etc.) where the
    related model has a reasonable number of instances.

    Important:
        This block is designed to be used with a model that has a many-to-many
        relationship with another model. The `field_name` must be set to the name
        of the many-to-many field on the model instance. The block will render a
        form that allows the user to select or deselect related objects.

        Also, this block requires that your model has a ``verbose_name_plural``
        method defined in its `Meta` class.

        We strongly recommend that you use the
        :py:class:`wildewidgets.ViewSetMixin` mixin in your model to provide the
        required attributes and methods for this block to work correctly.

    Example:
        .. code-block:: python

            from wildewidgets import ToggleableManyToManyFieldBlock
            from myapp.models import Article

            article = Article.objects.get(pk=1)  # Has many-to-many with 'tags'
            tags_widget = ToggleableManyToManyFieldBlock(
                instance=article,
                field_name='tags'
            )

    Args:
        instance: The model instance that has the many-to-many relationship

    Keyword Args:
        field_name: Name of the many-to-many field on the model instance
        form_class: Custom form class to use (must extend
            ``ToggleableManyToManyFieldForm)
        form_action: URL for form submission (if not provided, will be auto-generated)

    """

    #: The name of this block.
    name: str = "toggle-form-block"

    #: The JavaScript to run to hide unselected items and filter the list
    #: of items.
    #: The ``{target}`` placeholder will be replaced with the CSS id of the form
    #: that this block will render.
    #: The ``{filter_id}`` placeholder will be replaced with the CSS id of the
    #: filter input.
    #: The ``{show_unselected_id}`` placeholder will be replaced with the CSS id
    #: of the "Hide unselected" toggle switch.
    #: The JavaScript will hide all unselected items on page load, and will
    #: toggle the visibility of unselected items when the "Hide unselected" toggle
    #: is clicked.  It will also filter the list of items based on the text in
    #: the filter input.
    SCRIPT: Final[str] = """
document.querySelectorAll("{target} input.form-check-input").forEach(input => {{
    if (!input.checked) {{
        input.parentElement.classList.add('d-none');
    }};
}});
var show_input = document.getElementById("{show_unselected_id}");
show_input.onchange = function(e) {{
    document.querySelectorAll("{target} input.form-check-input").forEach(input => {{
        if (show_input.checked && !input.checked) {{
            input.parentElement.classList.add('d-none');
        }} else {{
            input.parentElement.classList.remove('d-none');
        }};
    }});
}};
var filter_input = document.getElementById("{filter_id}");
filter_input.onkeyup = function(e) {{
    var filter = filter_input.value.toLowerCase();
    show_input.checked = false
    document.querySelectorAll("{target} label").forEach(label => {{
        var test_string = label.innerText.toLowerCase();
        if (test_string.includes(filter)) {{
            label.parentElement.classList.remove('d-none');
        }} else {{
            label.parentElement.classList.add('d-none');
        }}
    }});
}};
"""

    #: The model this widget will be used with.  This is only used by our
    #: :py:meth:`as_v`
    model: type[Model] | None = None
    #: The name of the related field on our model instance for which we want to
    #: build this widget
    field_name: str | None = None
    #: The form class to instantiate to handle our multiple select
    form_class: type[Form] = ToggleableManyToManyFieldForm
    #: The URL to which to POST this form
    form_action: str | None = None
    #: The path prefix to use to root view.
    url_prefix: str = ""
    #: The URL namespace to use for our view name.  This should be set to
    #: the ``app_name`` set in the ``urls.py`` where this viewset's patterns
    #: will be added to ``urlpatterns``.
    url_namespace: str | None = None

    def __init__(
        self,
        instance: Model,
        field_name: str | None = None,
        form_class: type[Form] | None = None,
        form_action: str | None = None,
        **kwargs: Any,
    ) -> None:
        self.instance = instance
        self.model = instance.__class__
        if hasattr(self.model, "model_verbose_name_plural"):
            self.verbose_name_plural = self.model.model_verbose_name_plural()
        else:
            self.verbose_name_plural = self.model._meta.verbose_name_plural
            assert self.verbose_name_plural, (  # noqa: S101
                f"{self.model.__class__.__name__} msust have a "
                "verbose_name_plural in its Meta class"
            )
            if not self.verbose_name_plural[0].isupper():
                self.verbose_name_plural = self.verbose_name_plural.capitalize()
        self.field_name = field_name if field_name else self.field_name
        if self.field_name is None:
            msg = "field_name must be provided"
            raise ValueError(msg)
        self.field = self.instance._meta.get_field(self.field_name)
        self.related_model = self.field.related_model
        self.form_class = form_class if form_class else self.form_class
        self.form_action = form_action if form_action is not None else self.form_action
        if not self.form_action:
            url_name = self.get_url_name()
            if self.url_namespace:
                url_name = f"{self.url_namespace}:{url_name}"
            self.form_action = reverse(url_name, kwargs={"pk": self.instance.id})
        kwargs["script"] = self.SCRIPT.format(
            target=f"#{self.form_id}",
            filter_id=self.filter_id,
            show_unselected_id=self.show_all_switch_id,
        )
        super().__init__(self, **kwargs)
        self.set_header(self.get_header)
        self.set_widget(
            CrispyFormWidget(
                form=self.get_form(self.instance, self.field_name, self.form_action),
                css_id=self.form_id,
            )
        )

    @property
    def form_id(self) -> str:
        """
        Generate a unique CSS ID for the form element.

        This property creates a standardized ID by combining the model's object name
        with the field name. This ID is used for DOM selection in JavaScript and
        for linking form elements.

        Returns:
            str: A string in the format of "modelname_fieldname"

        Raises:
            AssertionError: If the model is not defined

        """
        assert self.model is not None, "self.model must be defined"  # noqa: S101
        return f"{self.model._meta.object_name.lower()}_{self.field_name}"  # type: ignore[union-attr]

    @property
    def filter_id(self) -> str:
        """
        Generate a unique CSS ID for the filter input element.

        This property appends "_filter" to the form_id to create a unique
        identifier for the search input field used to filter the list of items.

        Returns:
            str: A string in the format of "modelname_fieldname_filter"

        """
        return f"{self.form_id}_filter"

    @property
    def show_all_switch_id(self) -> str:
        """
        Generate a unique CSS ID for the "show all" toggle switch.

        This property appends "_show_all" to the form_id to create a unique
        identifier for the toggle switch that controls the visibility of
        unselected items.

        Returns:
            str: A string in the format of "modelname_fieldname_show_all"

        """
        return f"{self.form_id}_show_all"

    def get_form(self, instance: Model, field_name: str, form_action: str) -> Form:
        """
        Create and return a form for managing many-to-many relationships.

        This method instantiates a form of the class specified by the form_class
        attribute, binding it to the specified instance, field name, and form action.
        The form will be used to manage the many-to-many relationship between the
        instance and related model objects.

        Args:
            instance: The model instance to which the form will be bound
            field_name: The name of the many-to-many field on the model
            form_action: The URL to which the form will be submitted

        Returns:
            Form: An initialized form instance ready to be rendered

        """
        # We're expecting that the form_class is a subclass of
        # ToggleableManyToManyFieldForm, which has a constructor that accepts
        # instance, fields, and form_action.
        if not issubclass(self.form_class, ToggleableManyToManyFieldForm):
            msg = "form_class must be a subclass of ToggleableManyToManyFieldForm"
            raise TypeError(msg)
        return self.form_class(instance, fields=[field_name], form_action=form_action)

    def get_header(self) -> Block:
        """
        Get our card header.  This consists of a toggle switch which hides/shows
        unselected items and a search input that allows the user to search for
        items.

        Returns:
            The card header block.

        """
        # We have to do this import here due to circular dependencies
        from ..models import model_verbose_name_plural

        assert self.related_model is not None, (  # noqa: S101
            "self.related_model must be defined before calling get_header"
        )

        return HorizontalLayoutBlock(
            ToggleSwitchInputBlock(
                label_text="Hide unselected",
                input_name="hide-unchecked",
                value="hide",
                css_id=self.show_all_switch_id,
                css_class="pt-3",
                checked=True,
            ),
            Block(
                LabelBlock(
                    f"Filter {model_verbose_name_plural(self.related_model)}",
                    css_class="d-none",
                    attributes={
                        "for": self.filter_id,
                    },
                ),
                InputBlock(
                    attributes={
                        "type": "text",
                        "placeholder": f"Filter {model_verbose_name_plural(self.related_model)}",  # noqa: E501
                    },
                    css_id=self.filter_id,
                    css_class="form-control",
                ),
                css_class="w-25",
            ),
            justify="between",
            align="center",
            css_class="w-100",
        )

    @classmethod
    def get_url_name(cls) -> str:
        """
        Generate a standardized URL name for this widget's form submission endpoint.

        This method constructs a URL name by combining the model name and related model
        name in a standardized format. The URL name is used for routing form submissions
        to the appropriate view and follows the pattern:
        "{model_name}--{related_model_name}--update"

        The model names are converted to lowercase with underscores using the
        model_logger_name utility function.

        Returns:
            str: A URL name in the format "{model_name}--{related_model_name}--update"

        Raises:
            ValueError: If the model or field_name class attributes are not defined
            AssertionError: If the :py:attr:`related_model` is ``None``

        Note:
            This method requires that both the `model` and `field_name` class attributes
            are defined before calling.

        """
        from ..models import model_logger_name

        if cls.model is None:
            msg = "model must be defined before calling get_url_name"
            raise ValueError(msg)
        if cls.field_name is None:
            msg = "field_name must be defined before calling get_url_name"
            raise ValueError(msg)
        model_name = model_logger_name(cls.model)
        related_model = cls.model._meta.get_field(cls.field_name).related_model
        assert related_model is not None, (  # noqa: S101
            f"related_model on field {cls.field_name} must be defined"
        )
        related_model_name = model_logger_name(related_model)
        return f"{model_name}--{related_model_name}--update"

    @classmethod
    def get_urlpatterns(
        cls, url_prefix: str | None = None, url_namespace: str | None = None
    ) -> list[URLPattern]:
        """
        Build a view that will service this block and return a
        :py:class:`django.urls.URLPattern` for that view that you can add to
        your ``urlpatterns``.

        Example::

            from typing import List
            from django.urls import path, URLPattern

            from wildewidgets import ToggleableManyToManyFieldBlock

            from .views import HomeView
            from .models import MyModel

            class TagsSelectorWidget(ToggleableManyToManyFieldBlock):

                model = MyModel
                field_name = 'tags'

            app_name: str = "myapp"

            urlpatterns: List[URLPattern] = [
                path('', HomeView.as_view(), name='home'),
            ]
            urlpatterns += TagsSelectorWidget.get_urlpatterns(url_namespace=app_name)

        Important:
            In order for this to work, you must have subclassed
            :py:class:`ToggleableManyToManyFieldBlock` and defined both the
            :py:attr:`model` and :py:attr:`field_name` attributes.

        Keyword Args:
            url_prefix: a prefix to the path we will build for our view
            url_namespace: the namespace for our url pattern.  We'll set our
                :py:attr:`url_namespace` from this

        Returns:
            A list of urlpatterns for a view suitable for this block

        """
        from ..models import model_logger_name
        from ..views.generic import ManyToManyRelatedFieldView

        if cls.model is None:
            msg = 'Define the "model" class attribute before calling "get_urlpattern"'
            raise ValueError(msg)
        if cls.field_name is None:
            msg = (
                'Define the "field_name" class attribute before calling '
                '"get_urlpattern"'
            )
            raise ValueError(msg)
        model_name = model_logger_name(cls.model)
        related_model = cls.model._meta.get_field(cls.field_name).related_model
        assert related_model is not None, (  # noqa: S101
            f"related_model on field {cls.field_name} must be defined"
        )
        related_model_name = model_logger_name(related_model)
        if url_namespace:
            cls.url_namespace = url_namespace
        if not url_prefix:
            url_prefix = cls.url_prefix
        elif not url_prefix.endswith("/"):
            url_prefix = f"{url_prefix}/"
        view_path = path(
            f"{url_prefix}wildewidgets/{model_name}/<int:pk>/{related_model_name}/",
            ManyToManyRelatedFieldView.as_view(
                model=cls.model, field_name=cls.field_name
            ),
            name=cls.get_url_name(),
        )
        return [view_path]
