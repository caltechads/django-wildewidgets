from copy import copy, deepcopy

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from django.urls import reverse

from ..base import Block
from ..forms import HiddenInputBlock
from ..buttons import InputButton
from ..structure import HorizontalLayoutBlock

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


# -------------------------------
# Buttons
# -------------------------------

class RowActionButton(Block):

    tag: str = 'a'

    text: Optional[str] = None
    url: Optional[str] = None
    color: str = 'secondary'
    size: str = None
    permission: Optional[str] = None

    def __init__(
        self,
        text: str = None,
        url: str = None,
        color: str = None,
        size: str = None,
        permission: str = None,
        **kwargs
    ):
        self.text = text if text else self.text
        self.url = url if url else self.url
        self.color = color if color else self.color
        self.size = size if size else self.size
        self.permission = permission if permission else self.permission
        super().__init__(self.text, **kwargs)

        #: The table will set this
        self.row: Any = None

    def is_visible(self, row: Any, user: "Optional[AbstractUser]") -> bool:  # pylint: disable=arguments-differ
        if self.permission is not None and user is not None:
            if user.has_perm(self.permission):
                return True
            return False
        return True

    def get_url(self, row: Any) -> str:
        return self.url

    def bind(
        self,
        row: Any,
        table: "ActionButtonBlockMixin",
        size: str = None
    ) -> "RowActionButton":
        """
        Bind this button to a particular ``row``, and return the bound button.

        Note:
            We take ``table`` as an argument so that we can get access to attributes
            that are only on the containing table, e.g. ``csrf_token``, which is set
            during the AJAX call to our Table.

        Args:
            row: the row we're working on
            table: the DataTable instance that owns the row

        Keyword Args
            size: set the Bootstrap size of the button to this

        Returns:
            A copy of this button, bound to ``row``.
        """
        action = deepcopy(self)
        action.row = row
        action.add_class(f'btn-{self.color}')
        action._attributes['href'] = self.get_url(row)
        if not size:
            size = self.size
        if self.size:
            action.add_class(f'btn-{self.size}')
        return action


class RowLinkButton(RowActionButton):

    def get_context_data(self, *args, **kwargs) -> Dict[str, Any]:
        self._attributes['href'] = self.get_url(self.row)
        self._attributes['role'] = 'button'
        return super().get_context_data(*args, **kwargs)


class RowModelUrlButton(RowActionButton):

    block: str = 'btn'
    modifier: str = 'auto'

    attribute: str = 'get_absolute_url'
    text: Optional[str] = 'View'

    def __init__(
        self,
        attribute: str = None,
        **kwargs
    ):
        self.attribute = attribute if attribute else self.attribute
        super().__init__(**kwargs)

    def get_url(self, row: Any) -> str:
        if not hasattr(row, self.attribute):
            raise ValueError(
                f'{row} has no "{self.attribute}" attribute or method'
            )
        attr = getattr(row, self.attribute)
        if callable(attr):
            return attr()
        return attr


class RowDjangoUrlButton(RowActionButton):

    block: str = 'btn'

    url_path: Optional[str] = None
    url_args: List[str] = []
    url_kwargs: Dict[str, str] = {}

    def __init__(
        self,
        url_path: str = None,
        url_args: List[str] = None,
        url_kwargs: Dict[str, str] = None,
        **kwargs
    ):
        self.url_path = url_path if url_path else self.url_path
        self.url_args = url_args if url_args else copy(self.text)
        self.url_kwargs = url_kwargs if url_kwargs else copy(self.url_kwargs)
        if not self.url_path:
            raise self.RequiredAttrOrKwarg('url_path')
        if self.url_args and self.url_kwargs:
            raise ValueError(
                'Either "url_args" or "url_kwargs" must be provided as keyword arguments or '
                'class attributes, but not both'
            )
        super().__init__(**kwargs)

    def get_url(self, row: Any) -> str:
        if not (self.args and self.kwargs):
            url = reverse(self.url_path)
        if self.args:
            args = [getattr(row, arg) for arg in self.args]
            url = reverse(self.url_path, args=args)
        if self.kwargs:
            kwargs = {kwarg: getattr(self.row, attr) for kwarg, attr in self.kwargs}
            url = reverse(self.url_path, kwargs=kwargs)
        return url


class RowFormButton(RowModelUrlButton):

    block: str = 'action-form'
    tag: str = 'form'

    form_fields: List[str] = []
    confirm_text: str = None

    def __init__(
        self,
        form_fields: List[str] = None,
        confirm_text: str = None,
        **kwargs
    ):
        self.form_fields = form_fields if form_fields else deepcopy(self.form_fields)
        self.confirm_text = confirm_text if confirm_text else self.confirm_text
        super().__init__(**kwargs)
        # Our superclass added self.text as a block; but that will not work for us,
        # since we want self.text to be the button text, so remove it.
        self.blocks = []
        self._attributes['method'] = 'post'

    def get_confirm_text(self, row: Any) -> str:
        return self.confirm_text

    def bind(self, row: Any, table: Any, size: str = None) -> "RowFormButton":
        if not size:
            size = self.size
        action = deepcopy(self)
        action.add_block(HiddenInputBlock(input_name='csrfmiddlewaretoken', value=table.csrf_token))
        action._attributes['action'] = self.get_url(row)
        for field in self.form_fields:
            action.add_block(HiddenInputBlock(input_name=field, value=getattr(row, field)))
        action.add_block(
            InputButton(
                text=self.text,
                color=self.color,
                size=size,
                confirm_text=self.get_confirm_text(row)
            )
        )
        return action


class RowEditButton(RowModelUrlButton):

    attribute: str = 'get_update_url'
    text: str = 'Edit'
    color: str = 'primary'


class RowDeleteButton(RowFormButton):

    attribute: str = 'get_delete_url'
    text: str = 'Delete'
    color: str = 'outline-secondary'
    form_fields: List[str] = ['id']

    def get_confirm_text(self, row: Any) -> str:
        return f'Delete "{str(row)}"?'


# -------------------------------
# Mixins
# -------------------------------

class ActionsButtonsBySpecMixin:
    """
    This is a mixin class for :py:class:`DataTable` classes that allows you to specify
    buttons that will appear per row in an "Actions" column, rightmost of all columns.

    If :py:attr:`actions` is ``True``, and a row object has an attribute or
    method named ``get_absolute_url``,  render a single button named
    :py:attr:`default_action_button_label` that when clicked takes the user
    to that URL.

    Otherwise, :py:attr:`actions` should be a iterable of tuples or lists of
    the following structures::

        (label, Django URL name)
        (label, Django URL name, 'get' or 'post')
        (label, Django URL name, 'get' or 'post', color)
        (label, Django URL name, 'get' or 'post', color)
        (label, Django URL name, 'get' or 'post', color, pk_field_name)
        (label, Django URL name, 'get' or 'post', color, pk_field_name, javascript function name)

    Note:
        The magic is all done in :py:meth:`render_actions_column`, so if you want
        to see what's really going on, read that code.

    Examples:

        To make a button named "Edit" that goes to the django URL named
        ``core:model--edit``::

            ('Edit', 'core:model--edit')

        This renders a "button" something like this::

            <a href="/core/model/edit/?id=1" class="btn btn-secondary me-2">Edit</a>

        Make a button named "Delete" that goes to the django URL named
        ``core:model--delete`` as a ``POST``::

            ('Delete', 'core:model--delete', 'post')

        This renders a "button" something like this::

            <form class"form form-inline" action="/core/model/delete/" method="post">
                <input type="hidden" name="csrfmiddlewaretoken" value="__THE_TOKEN__">
                <input type="hidden" name="id" value="1">
                <input type="submit" value="Delete" class="btn btn-secondary me-2">
            </form>
    """

    #: Per row action buttons.  If not ``False``, this will simply add a
    #: rightmost column  named ``Actions`` with a button named
    #: :py:attr:`default_action_button_label` which when clicked will take the
    #: user to the
    actions: Any = False
    #: How big should each action button be? One of ``normal``, ``btn-lg``, or ``btn-sm``.
    action_button_size: str = 'normal'
    #: The label to use for the default action button
    default_action_button_label: str = 'View'
    #: The Bootstrap color class to use for the default action buttons
    default_action_button_color_class: str = 'secondary'

    def __init__(
        self,
        *args,
        actions: Any = None,
        action_button_size: str = None,
        default_action_button_label: str = None,
        default_action_button_color_class: str = None,
        **kwargs
    ):
        self.actions = actions if actions is not None else self.actions
        self.action_button_size = action_button_size if action_button_size else self.action_button_size
        self.default_action_button_label = (
            default_action_button_label
            if default_action_button_label else self.default_action_button_label
        )
        self.default_action_button_color_class = (
            default_action_button_color_class
            if default_action_button_color_class else self.default_action_button_color_class
        )
        if self.action_button_size != 'normal':
            self.action_button_size_class = f"btn-{self.action_button_size}"
        else:
            self.action_button_size_class = ''
        super().__init__(*args, **kwargs)

    def get_template_context_data(self, **kwargs) -> Dict[str, Any]:
        if self.actions:
            self.add_column(field='actions', searchable=False, sortable=False)
            kwargs['has_actions'] = True
            kwargs['action_column'] = len(self.column_fields) - 1
        else:
            kwargs['has_actions'] = False
        return super().get_template_context_data(**kwargs)

    def get_content(self, **kwargs) -> str:
        if self.actions:
            self.add_column(field='actions', searchable=False, sortable=False)
        return super().get_content(**kwargs)

    def get_action_button(
        self,
        row: Any,
        label: str,
        url_name: str,
        method: str = 'get',
        color_class: str = 'secondary',
        attr: str = 'id',
        js_function_name: str = None
    ) -> str:
        if url_name:
            base = reverse(url_name)
            # FIXME: This assumes we're using QueryStringKwargsMixin, which people
            # outside our group don't use
            if method == 'get':
                url = f"{base}?{attr}={row.id}"
            else:
                url = base
        else:
            url = "javascript:void(0)"
        return self.get_action_button_with_url(row, label, url, method, color_class, attr, js_function_name)

    def get_action_button_url_extra_attributes(self, row: Any) -> str:
        return ""

    def get_action_button_with_url(
        self,
        row: Any,
        label: str,
        url: str,
        method: str = 'get',
        color_class: str = 'secondary',
        attr: str = 'id',
        js_function_name: str = None
    ) -> str:
        url_extra = self.get_action_button_url_extra_attributes(row)
        if url_extra:
            url = f"{url}&{url_extra}"
        if method == 'get':
            if js_function_name:
                link_extra = f'onclick="{js_function_name}({row.id});"'
            else:
                link_extra = ""
            return f'<a href="{url}" class="btn btn-{color_class} {self.action_button_size_class} me-2" {link_extra}>{label}</a>'
        token_input = f'<input type="hidden" name="csrfmiddlewaretoken" value="{self.csrf_token}">'
        id_input = f'<input type="hidden" name="{attr}" value="{row.id}">'
        button = f'<input type=submit value="{label}" class="btn btn-{color_class} {self.action_button_size_class} me-2">'
        form = f'<form class="form form-inline" action={url} method="post">{token_input}{id_input}{button}</form>'
        return form

    def get_conditional_action_buttons(self, row: Any) -> str:
        return ''

    def render_actions_column(self, row: Any, column: str) -> str:
        """
        Render the buttons in the "Actions" column.  This will only be called if
        :py:attr:`actions` is not falsy.  We rely on :py:attr:`actions` to be
        specified in a particular way in order for this to work; see
        :py:class:`ActionButtonsBySpecMixin` for information about how to
        specify button specs in :py:attr:`actions` is constructed.

        Args:
            row: the row data for which we are building action buttons
            column: unused

        Returns:
            The HTML to render into the "Actions" column for ``row``.
        """
        response = '<div class="d-flex flex-row justify-content-end">'
        if hasattr(row, 'get_absolute_url'):
            if callable(row.get_absolute_url):
                url = row.get_absolute_url()
            else:
                url = row.get_absolute_url
            view_button = self.get_action_button_with_url(
                row,
                self.default_action_button_label,
                url,
                color_class=self.default_action_button_color_class
            )
            response += view_button
        if not isinstance(self.actions, bool):
            for action in self.actions:
                if not len(action) > 1:
                    continue
                label = action[0]
                url_name = action[1]
                if len(action) > 2:
                    method = action[2]
                else:
                    method = 'get'
                if len(action) > 3:
                    color_class = action[3]
                else:
                    color_class = 'secondary'
                if len(action) > 4:
                    attr = action[4]
                else:
                    attr = 'id'
                if len(action) > 5:
                    js_function_name = action[5]
                else:
                    js_function_name = ''
                response += self.get_action_button(row, label, url_name, method, color_class, attr, js_function_name)
        response += self.get_conditional_action_buttons(row)
        response += "</div>"
        return response


class ActionButtonBlockMixin:
    """
    This is a mixin class for dataTable classes that allows you to specify
    buttons that will appear per row in an "Actions" column, rightmost of all
    columns.

    """

    #: If not ``None``, make all per-row action buttons be this size.
    button_size: Optional[str] = None
    justify: str = 'end'

    actions: List[RowActionButton] = [
        RowModelUrlButton(text='View', color='secondary')
    ]

    def __init__(
        self,
        *args,
        actions: List[RowActionButton] = None,
        button_size: str = None,
        justify: str = None,
        **kwargs
    ):
        self.actions = actions if actions is not None else deepcopy(self.actions)
        self.button_size = button_size if button_size else self.button_size
        self.justify = justify if justify else self.justify
        super().__init__(*args, **kwargs)

    def get_actions(self) -> List[RowActionButton]:
        return self.actions

    def get_content(self, **kwargs) -> str:
        if self.get_actions():
            self.add_column(field='actions', searchable=False, sortable=False)
        return super().get_content(**kwargs)

    def render_actions_column(self, row: Any, column: str) -> str:
        container = HorizontalLayoutBlock(justify=self.justify)
        for action in self.get_actions():
            button = action.bind(row, self, size=self.button_size)
            user = None
            if hasattr(self, 'request') and self.request is not None:
                user = self.request.user
            if not button.is_visible(row, user):
                continue
            button.add_class('me-2')
            container.add_block(button)
        button.remove_class('me-2')
        return str(container)


class StandardModelActionButtonBlockMixin(ActionButtonBlockMixin):
    """
    This is an :py:class:`ActionButtonBlockMixin` that supplies an "Edit" and
    "Delete" button for each row.

    Important:

        For this to work, use the
        :py:class:`wildewidgets.models.ViewSetMixin` on your model, and
        define the ``get_update_url`` and ``get_delete_url`` methods.
    """

    actions: List[RowActionButton] = [
        RowModelUrlButton(text='Edit', color='primary', attribute='get_update_url'),
        RowModelUrlButton(text='delete', color='outline-secondary', attribute='get_delete_url'),
    ]
