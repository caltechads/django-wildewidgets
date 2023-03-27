from typing import List, Optional, Type

from django.db.models import Model
from django.forms import Form
from django.urls import path, URLPattern, reverse

from ..forms import ToggleableManyToManyFieldForm

from .base import Block
from .structure import CardWidget, HorizontalLayoutBlock


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
    for_input: Optional[str] = None

    def __init__(
        self,
        text: str,
        for_input: str = None,
        bold: bool = None,
        color: str = "secondary",
        **kwargs
    ):
        # FIXME: color is a kwarg, but it is not used
        self.bold = bold if bold is not None else self.bold
        self.for_input = for_input if for_input is not None else self.for_input
        super().__init__(text, **kwargs)
        if self.for_input:
            self._attributes['for'] = self.for_input
        if self.bold:
            self.add_class('fw-bold')


class InputBlock(Block):
    """
    A block for rendering a simple ``<input>`` element.

    Example:

        >>> block = InputBlock(input_type='checkbox', input_name='my-checkbox', value=1)

    Keyword Args:
        input_type: the value of the ``type`` attribute
        input_name: the value of the ``name`` attribute
        value: the value of the ``value`` attribute
    """
    empty: bool = True
    tag: str = 'input'

    input_type: Optional[str] = None
    input_name: Optional[str] = None
    value: Optional[str] = None

    def __init__(
        self,
        input_type: str = None,
        input_name: str = None,
        value: str = None,
        **kwargs
    ):
        self.input_type = input_type if input_type else self.input_type
        self.input_name = input_name if input_name else self.input_name
        self.value = value if value else self.value
        super().__init__(**kwargs)
        if self.input_type is not None:
            self._attributes['type'] = self.input_type
        if self.input_name is not None:
            self._attributes['name'] = self.input_name
        if self.value is not None:
            self._attributes['value'] = self.value


class BaseCheckboxInputBlock(InputBlock):
    """
    A block for rendering a bare ``<input type="checkbox">`` element.

    Example:

        >>> block = BaseCheckboxInputBlock(name='my-checkbox', value=1)
        >>> block = BaseCheckboxInputBlock(name='my-checkbox', value=1, checked=true)

    Keyword Args:
        checked: if ``True``, render the checkbox as checked
    """

    input_type: str = 'checkbox'

    def __init__(
        self,
        checked: bool = False,
        **kwargs
    ):
        self.checked = checked
        super().__init__(**kwargs)
        if not self.input_name:
            raise self.RequiredAttrOrKwarg('input_name')
        if not self.value:
            raise self.RequiredAttrOrKwarg('value')
        if self.checked:
            self._attributes['checked'] = ''


class CheckboxInputBlock(Block):
    """
    A block for rendering a ``<input type="checkbox">`` element with a label as a
    `Boostrap 5 check <https://getbootstrap.com/docs/5.2/forms/checks-radios/#checks>`_.

    Example:

        >>> block = CheckboxInputBlock(label_text='My Checkbox', name='my-checkbox', value=1)

    Keyword Args:
        label_text: the text to use for the label
        bold: if ``True``, make the label text be bold
        input_name: the value of the ``name`` attribute
        value: the value of the ``value`` attribute
        checked: if ``True``, render the checkbox as checked
    """

    #: the value of the ``name`` attribute
    input_name: Optional[str] = None
    #: the value of the ``value`` attribute
    value: Optional[str] = None
    #: the text to use for the label
    label_text: Optional[str] = None
    #: if ``True``, make the label text be bold
    bold: bool = True

    def __init__(
        self,
        label_text: str = None,
        bold: bool = None,
        input_name: str = None,
        value: str = None,
        checked: bool = False,
        **kwargs
    ):
        self.label_text = label_text if label_text else self.label_text
        self.input_name = input_name if input_name else self.input_name
        self.bold = bold if bold is not None else self.bold
        self.value = value if value else self.value
        if not self.label_text:
            raise self.RequiredAttrOrKwarg('label_text')
        if not self.input_name:
            raise self.RequiredAttrOrKwarg('input_name')
        if not self.value:
            raise self.RequiredAttrOrKwarg('value')
        self.input_css_id = kwargs.pop('css_id', f'checkbox-{self.input_name}-{self.value}')
        self.checked = checked
        super().__init__(**kwargs)
        self.add_class('form-check')
        self.add_block(
            BaseCheckboxInputBlock(
                input_name=self.input_name,
                value=self.value,
                css_id=self.input_css_id,
                checked=self.checked,
                css_class='form-check-input'
            )
        )
        self.add_block(
            LabelBlock(
                text=self.label_text,
                bold=self.bold,
                for_input=self.input_css_id,
                css_class='form-check-label'
            )
        )


class ToggleSwitchInputBlock(CheckboxInputBlock):
    """
    A block for rendering a ``<input type="checkbox">`` element with a label as
    a `Bootstrap 5 switch <https://getbootstrap.com/docs/5.0/forms/checks-radios/#switches>`_.

    Example:

        >>> block = ToggleSwitchInputBlock(label_text='My Checkbox', name='my-checkbox', value=1)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_class('form-switch')


class HiddenInputBlock(InputBlock):
    """
    A block for rendering a ``<input type="hidden">``.

    Example:

        >>> block = HiddenInputBlock(name='my-checkbox', value=1)
    """

    input_type: str = 'hidden'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.input_name:
            raise self.RequiredAttrOrKwarg('input_name')
        if not self.value:
            raise self.RequiredAttrOrKwarg('value')


class CrispyFormWidget(Block):
    """
    A widget that displays a Crispy Form widget.  This is specifically a Crispy
    Form widget because it uses the ``{% crispy %}`` template tag to render the
    form.

    Note:

        If the form is present in the template context already, (because your
        view inserted it for you) you don't need to supply the :py:attr:`form`
        keyword argument -- :py:class:`CrispyFormWidget` will pick it up
        automatically.

    Keyword Args:
        form: A crispy form to display. If none is specified, it will be assumed
            that ``form`` is specified elsewhere in the context.
    """
    template_name: str = 'wildewidgets/crispy_form_widget.html'
    block: str = "wildewidgets-crispy-form-widget"

    def __init__(self, *blocks, form: Form = None, **kwargs):
        super().__init__(*blocks, **kwargs)
        self.form = form

    def get_context_data(self, *args, **kwargs):
        kwargs = super().get_context_data(*args, **kwargs)
        if self.form:
            kwargs['form'] = self.form
        return kwargs


class ToggleableManyToManyFieldBlock(CardWidget):
    """
    This is a block that allows you to manage a many to many relationship
    between a model and a related model as a list of toggleable items.  The
    block lists all available items, showing which ones are selected on our
    model instance as checked toggle switches.  It also offers a search box
    to search for items in the list, and a control to hide unselected items.

    This is mostly appropriate for relationships between a model and a
    list-of-values type lookup table (e.g. categories, tags, classifiers, etc.).

    Keyword Args:
    """

    name: str = 'toggle-form-block'

    SCRIPT: str = """
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
    model: Optional[Type[Model]] = None
    #: The name of the related field on our model instance for which we want to
    #: build this widget
    field_name: Optional[str] = None
    #: The form class to instantiate to handle our multiple select
    form_class: Type[Form] = ToggleableManyToManyFieldForm
    #: The URL to which to POST this form
    form_action: Optional[str] = None
    #: The path prefix to use to root view.
    url_prefix: str = ''
    #: The URL namespace to use for our view name.  This should be set to
    #: the ``app_name`` set in the ``urls.py`` where this viewset's patterns
    #: will be added to ``urlpatterns``.
    url_namespace: Optional[str] = None

    def __init__(
        self,
        instance: Model,
        field_name: str = None,
        form_class: Type[Form] = None,
        form_action: str = None,
        **kwargs
    ):
        self.instance = instance
        self.model = instance.__class__
        if hasattr(self.model, 'model_verbose_name_plural'):
            self.verbose_name_plural = self.model.model_verbose_name_plural()
        else:
            self.verbose_name_plural = self.model._meta.verbose_name_plural
            if not self.verbose_name_plural[0].isupper():
                self.verbose_name_plural = self.verbose_name_plural.capitalize()
        self.field_name = field_name if field_name else self.field_name
        self.field = self.instance._meta.get_field(self.field_name)
        self.related_model = self.field.related_model
        self.form_class = form_class if form_class else self.form_class
        self.form_action = form_action if form_action is not None else self.form_action
        if not self.form_action:
            url_name = self.get_url_name()
            if self.url_namespace:
                url_name = f'{self.url_namespace}:{url_name}'
            self.form_action = reverse(url_name, kwargs={'pk': self.instance.id})
        kwargs['script'] = self.SCRIPT.format(
            target=f'#{self.form_id}',
            filter_id=self.filter_id,
            show_unselected_id=self.show_all_switch_id
        )
        super().__init__(self, **kwargs)
        self.set_header(self.get_header)
        self.set_widget(
            CrispyFormWidget(
                form=self.get_form(self.instance, self.field_name, self.form_action),
                css_id=self.form_id
            )
        )

    @property
    def form_id(self) -> str:
        """
        Return the CSS id we should use for our form.
        """
        return f'{self.model._meta.object_name.lower()}_{self.field_name}'

    @property
    def filter_id(self) -> str:
        """
        Return the CSS id we should use for the filter items search input.
        """
        return f'{self.form_id}_filter'

    @property
    def show_all_switch_id(self) -> str:
        """
        Return the CSS id we should for our "Hide unselected" toggle.
        """
        return f'{self.form_id}_show_all'

    def get_form(
        self,
        instance: Model,
        field_name: str,
        form_action: str
    ) -> Form:
        """
        Return the form to render into our widget, bound to ``field_name`` on
        ``instance``.

        Args:
            instance: the model instance to which to bind our form
            field_name: the name of our many-to-many field on our model
            form_action: the URL to which to POST our form

        Returns:
            An instance of :py:attr:`form_class` bound to ``instance``.
        """
        return self.form_class(instance, field_name=field_name, form_action=form_action)

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
        return HorizontalLayoutBlock(
            ToggleSwitchInputBlock(
                label_text="Hide unselected",
                input_name='hide-unchecked',
                value='hide',
                css_id=self.show_all_switch_id,
                css_class='pt-3',
                checked=True
            ),
            Block(
                LabelBlock(
                    f'Filter {model_verbose_name_plural(self.related_model)}',
                    css_class="d-none",
                    attributes={
                        'for': self.filter_id,
                    },
                ),
                InputBlock(
                    attributes={
                        'type': 'text',
                        'placeholder': f'Filter {model_verbose_name_plural(self.related_model)}',
                    },
                    css_id=self.filter_id,
                    css_class='form-control',
                ),
                css_class='w-25',
            ),
            justify='between',
            align='center',
            css_class='w-100'
        )

    @classmethod
    def get_url_name(cls) -> str:
        from ..models import model_logger_name
        model_name = model_logger_name(cls.model)
        related_model = cls.model._meta.get_field(cls.field_name).related_model
        related_model_name = model_logger_name(related_model)
        return f'{model_name}--{related_model_name}--update'

    @classmethod
    def get_urlpatterns(cls, url_prefix: str = None, url_namespace: str = None) -> List[URLPattern]:
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
        from ..views.generic import ManyToManyRelatedFieldView
        from ..models import model_logger_name
        if cls.model is None:
            raise ValueError('Define the "model" class attribute before calling "get_urlpattern"')
        if cls.field_name is None:
            raise ValueError('Define the "field_name" class attribute before calling "get_urlpattern"')
        model_name = model_logger_name(cls.model)
        related_model = cls.model._meta.get_field(cls.field_name).related_model
        related_model_name = model_logger_name(related_model)
        if url_namespace:
            cls.url_namespace = url_namespace
        if not url_prefix:
            url_prefix = cls.url_prefix
        elif not url_prefix.endswith('/'):
            url_prefix = f'{url_prefix}/'
        view_path = path(
            f'{url_prefix}wildewidgets/{model_name}/<int:pk>/{related_model_name}/',
            ManyToManyRelatedFieldView.as_view(model=cls.model, field_name=cls.field_name),
            name=cls.get_url_name()
        )
        return [view_path]
