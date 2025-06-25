from __future__ import annotations

from copy import copy, deepcopy
from typing import TYPE_CHECKING, Any, Literal, cast

from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse

from ..base import Block
from ..buttons import InputButton
from ..forms import HiddenInputBlock
from ..structure import HorizontalLayoutBlock

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.contrib.auth.models import AbstractUser


# -------------------------------
# Buttons
# -------------------------------


class RowActionButton(Block):
    """
    Base class for action buttons displayed in table rows.

    This class provides the foundation for creating buttons that appear in the
    "Actions" column of tables. Each button is bound to a specific row and can
    perform actions based on that row's data. Note that all keyword arguments/class
    attributes from :py:class:`wildewidgets.Block` are also accepted.

    You can use this class directly with keyword arguments to create buttons
    that link to row-specific URLs. In order for this to work, you'll need to
    pass a callable into `url` that accepts a single argument, which will be
    the row data. This callable should return a string that is the URL for
    the button.

    You will more usually subclass this, setting class attributes to create
    specific model-based buttons, and overriding the :py:meth:`get_url` method
    to return the URL for the button based on the row data.

    Attributes:
        tag: HTML tag for the button, defaults to "a" for links
        text: The text displayed on the button
        url: The URL the button links to, a Django URL name to reverse, or a callable
            that accepts a ``row`` arg and returns a URL string
        color: Bootstrap color class for the button (e.g., "primary", "secondary")
        size: Bootstrap size class for the button (e.g., "sm", "lg")
        permission: Optional Django permission string required to see the button
        row: Reference to the row data this button is bound to (set by bind method)

    Example:
        Direct usage with keyword arguments:

        .. code-block:: python

            from django.urls import reverse
            from wildewidgets import RowActionButton

            def get_home_url(row: Any) -> str:
                return reverse("app:home", kwargs={"id": row.id})

            button = RowActionButton(
                text="Home",
                url=get_home_url,
                color="primary",
                permission="app.view_item"
            )

        Subclassing for specific actions:

        .. code-block:: python

            class RowViewButton(RowActionButton):
                text = "View"
                color = "info"
                size = "sm"
                url = "core:item-view"

                def get_url(self, row: Any) -> str:
                    return reverse(self.url, kwargs={"id": row.id})

    Keyword Args:
        text: The text to display on the button
        url: The URL the button should link to
        color: The Bootstrap color class for the button (default: "secondary")
        size: The Bootstrap size class for the button (default: None)
        permission: Optional Django permission string required to see this
            button, e.g. "app.view_item"
        **kwargs: Additional attributes passed to the parent Block class

    Raises:
        ImproperlyConfigured: If 'text' or 'url' is not provided

    """

    tag: str = "a"

    text: str | None = None
    url: str | Callable[[Any], str] | None = None
    color: str = "secondary"
    size: str | None = None
    permission: str | None = None

    def __init__(
        self,
        text: str | None = None,
        url: str | Callable[[Any], str] | None = None,
        color: str | None = None,
        size: str | None = None,
        permission: str | None = None,
        **kwargs,
    ):
        self.text = text if text else self.text
        self.url = url if url else self.url
        self.color = color if color else self.color
        self.size = size if size else self.size
        self.permission = permission if permission else self.permission
        super().__init__(cast("str", self.text), **kwargs)

        #: The table will set this
        self.row: Any = None

    def is_visible(self, row: Any, user: AbstractUser | None) -> bool:  # type: ignore[override]  # noqa: ARG002
        """
        Determine if this button should be visible to the given user.

        Args:
            row: The row data this button is associated with
            user: The current Django user

        Returns:
            bool: True if the button should be visible, False otherwise

        Note:
            If a permission is specified, the user must have that permission
            for the button to be visible.

        """
        if self.permission is not None and user is not None:
            return bool(user.has_perm(self.permission))
        return True

    def get_url(self, row: Any) -> str:
        """
        Get the URL for this button, potentially based on row data.

        This base implementation simply returns the static URL property.
        Subclasses can override this to generate dynamic URLs based on row data.

        Args:
            row: The row data to use for URL generation

        Returns:
            str: The URL for the button

        """
        if callable(self.url):
            # If the URL is a callable, call it with the row data
            return self.url(row)
        return self.url  # type: ignore[return-value]

    def bind(
        self,
        row: Any,
        table: ActionButtonBlockMixin,  # noqa: ARG002
        size: str | None = None,
    ) -> RowActionButton:
        """
        Bind this button to a specific row and return a copy configured for that
        row.

        This method creates a copy of the button configured specifically for the
        given row, including setting appropriate URLs, colors and sizes.

        Args:
            row: The row data to bind this button to
            table: The table instance that contains this row
            size: Optional size override for the button

        Returns:
            RowActionButton: A new button instance bound to the specified row

        Note:
            The table parameter provides access to table-level properties
            like CSRF tokens needed for form submissions.

        """
        action = deepcopy(self)
        action.row = row
        action.add_class(f"btn-{self.color}")
        action._attributes["href"] = self.get_url(row)
        if not size:
            size = self.size
        if self.size:
            action.add_class(f"btn-{self.size}")
        return action


class RowLinkButton(RowActionButton):
    """
    A row action button that renders as a link with appropriate attributes.

    This subclass of :py:class:`RowActionButton` ensures the rendered button has
    the appropriate attributes for accessibility and behavior as a link.

    Either subclass this, setting class attributes to create specific
    model-based buttons, or use it directly with keyword arguments to create
    buttons that link to model-specific URLs.  Note that all keyword
    arguments/class attributes from :py:class:`wildewidgets.Block`  and
    :py:class:`RowActionButton` are also accepted.

    Note:
        If ``row`` is going to be a Django model instance, you're better off
        using :py:class:`RowModelUrlButton` or :py:class:`RowDjangoUrlButton`
        instead.

        Honestly, the only difference between this and :py:class:`RowActionButton`
        is that we set the ``role`` attribute on the `<a>` tag to "button".

    Attributes:
        Inherits all attributes from :py:class:`RowActionButton`.

    Example:
        Direct usage with keyword arguments:

        .. code-block:: python

            from django.urls import reverse

            from wildewidgets import RowLinkButton

            def get_details_url(row: Any) -> str:
                return reverse("app:item-details", kwargs={"id": row.id})

            button = RowLinkButton(
                text="Details",
                url=get_details_url,
                color="info"
            )

        Subclassing for specific actions:

        .. code-block:: python

            from django.urls import reverse_lazy
            from wildewidgets import RowLinkButton

            class RowDetailsButton(RowLinkButton):
                text = "Details"
                color = "info"

                def get_url(self, row: Any) -> str:
                    return reverse("app:item-details", kwargs={"id": row.id})


    """

    def get_context_data(self, *args, **kwargs) -> dict[str, Any]:
        """
        Prepare the context data for template rendering.

        Sets appropriate attributes for accessibility including href and role.

        Args:
            *args: Positional arguments passed to the parent method
            **kwargs: Keyword arguments passed to the parent method

        Returns:
            dict: The context dictionary with updated attributes

        """
        self._attributes["href"] = self.get_url(self.row)
        self._attributes["role"] = "button"
        return super().get_context_data(*args, **kwargs)


class RowModelUrlButton(RowActionButton):
    """
    A row action button that gets its URL from a model instance attribute or
    method.

    This button uses a specified attribute or method of the row's model instance
    to determine its URL, making it ideal for standard model actions like view
    or edit.

    Either subclass this, setting class attributes to create specific
    model-based buttons, or use it directly with keyword arguments to create
    buttons that link to model-specific URLs.  Note that all keyword
    arguments/class attributes from :py:class:`wildewidgets.Block` and
    :py:class:`RowActionButton` are also accepted.

    Attributes:
        block: CSS class for styling ("btn")
        modifier: CSS modifier class ("auto")
        attribute: The model attribute or method to use for URL generation. Your model
            must implement this method or attribute to return the URL.
        text: Default button text ("View")

    Example:
        Direct usage with keyword arguments:

        .. code-block:: python

            from wildewidgets import RowModelUrlButton

            # Uses row.get_absolute_url() to determine URL
            button = RowModelUrlButton(text="View Details")

            # Uses row.get_edit_url() to determine URL
            button = RowModelUrlButton(
                text="Edit",
                attribute="get_edit_url",
                color="primary"
            )

        Subclassing for specific actions:

        .. code-block:: python

            class RowViewButton(RowModelUrlButton):
                attribute = "get_absolute_url"
                text = "View"
                color = "info"
                size = "sm"

    Keyword Args:
        attribute: The model attribute or method to use for URL generation. Your model
            must implement this method or attribute to return the URL.
        **kwargs: Additional keyword arguments for the
            *:py:class:`RowActionButton` class

    """

    block: str = "btn"
    modifier: str = "auto"

    attribute: str = "get_absolute_url"
    text: str | None = "View"

    def __init__(self, attribute: str | None = None, **kwargs):
        self.attribute = attribute if attribute else self.attribute
        super().__init__(**kwargs)

    def get_url(self, row: Any) -> str:
        """
        Get the URL from the specified model attribute or method.

        Args:
            row: The model instance to get the URL from

        Returns:
            str: The URL for the button

        Raises:
            ValueError: If the specified attribute doesn't exist on the model

        """
        if not hasattr(row, self.attribute):
            msg = f'{row} has no "{self.attribute}" attribute or method'
            raise ValueError(msg)
        attr = getattr(row, self.attribute)
        if callable(attr):
            return attr()
        return attr


class RowDjangoUrlButton(RowActionButton):
    """
    A row action button that constructs its URL using Django's URL resolver.

    This button uses Django's URL resolution system with either positional
    or keyword arguments to construct its URL dynamically based on row data.

    Either subclass this, setting class attributes to create specific
    model-based buttons, or use it directly with keyword arguments to create
    buttons that link to model-specific URLs.  Note that all keyword
    arguments/class attributes from :py:class:`wildewidgets.Block`  and
    :py:class:`RowActionButton` are also accepted.

    Attributes:
        block: CSS class for styling ("btn")
        url_path: The Django URL pattern name to reverse, e.g., "app:item-edit"
        url_args: List of row attribute names to use as positional arguments
        url_kwargs: Dictionary mapping URL param names to row attribute names

    Example:
        Direct usage with keyword arguments:

        .. code-block:: python

            from wildewidgets import RowDjangoUrlButton

            # Using positional arguments (e.g., 'item/1/')
            button = RowDjangoUrlButton(
                text="Edit",
                url_path="app:item-edit",
                url_args=["id"]
            )

            # Using keyword arguments (e.g., 'item/edit/?pk=1')
            button = RowDjangoUrlButton(
                text="Edit",
                url_path="app:item-edit",
                url_kwargs={"pk": "id"}
            )

        Subclassing for specific actions:

        .. code-block:: python

            class RowEditButton(RowDjangoUrlButton):
                url_path = "app:item-edit"
                text = "Edit"
                color = "primary"
                url_args = ["id"]

    Note:
        You must specify either ``url_args`` or ``url_kwargs``, but not both.

    Keyword Args:
        url_path: The Django URL pattern name to reverse
        url_args: List of row attribute names to use as positional arguments
        url_kwargs: Dictionary mapping URL param names to row attribute names

    Raises:
        ImproperlyConfigured: If both ``url_args`` and ``url_kwargs`` are provided,
            or if url_path is not set
        RowActionButton.RequiredAttrOrKwarg: If url_path is not set

    """

    block: str = "btn"

    url_path: str | None = None
    url_args: list[str] = []  # noqa: RUF012
    url_kwargs: dict[str, str] = {}  # noqa: RUF012

    def __init__(
        self,
        url_path: str | None = None,
        url_args: list[str] | None = None,
        url_kwargs: dict[str, str] | None = None,
        **kwargs,
    ):
        self.url_path = url_path if url_path else self.url_path
        self.url_args = url_args if url_args else copy(self.url_args)
        self.url_kwargs = url_kwargs if url_kwargs else copy(self.url_kwargs)
        if not self.url_path:
            msg = "url_path"
            raise self.RequiredAttrOrKwarg(msg)
        if self.url_args and self.url_kwargs:
            msg = (
                'Either "url_args" or "url_kwargs" must be provided as keyword '
                "arguments or class attributes, but not both"
            )
            raise ImproperlyConfigured(msg)
        super().__init__(**kwargs)

    def get_url(self, row: Any) -> str:
        """
        Construct a URL using Django's URL resolver with row data.

        Args:
            row: The row data to use for URL parameters

        Returns:
            str: The resolved URL for the button

        """
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
    """
    A row action button that renders as a form, submitting via POST.

    This button renders as an HTML form that submits via POST when clicked.
    It's ideal for actions that modify data, like delete or status change
    operations.  You do not need to provide a form -- it will be created
    automatically.

    Either subclass this, setting class attributes to create specific
    model-based buttons, or use it directly with keyword arguments to create
    buttons that link to model-specific URLs.  Note that all keyword
    arguments/class attributes from :py:class:`wildewidgets.Block`  and
    :py:class:`RowModelUrlButton` are also accepted.

    Attributes:
        block: CSS class for styling ("action-form")
        tag: HTML tag for the container ("form")
        form_fields: List of row attribute names to include as hidden fields
        confirm_text: Confirmation message to show before submission

    Example:
        Direct usage with keyword arguments:

        .. code-block:: python

            from wildewidgets import RowFormButton

            button = RowFormButton(
                text="Delete",
                attribute="get_delete_url",
                form_fields=["id"],
                confirm_text="Are you sure you want to delete this item?"
            )

        Subclassing for specific actions:

        .. code-block:: python

            class RowDeleteButton(RowFormButton):
                attribute = "get_delete_url"
                text = "Delete"
                color = "outline-secondary"
                form_fields = ["id"]
                confirm_text = "Are you sure you want to delete this item?"

    Note:
        - Requires both form_fields and confirm_text to be specified
        - Will include CSRF token automatically
        - The form action URL is determined by the :py:attr:`attribute` method
          or attribute, which must be present on the model class.  If you need
          more sophisticated URL handling, subclass and override the
          :py:meth:`get_url` method.


    Keyword Args:
        form_fields: List of row attribute names to include as hidden fields
        confirm_text: Confirmation message to show before submission

    Raises:
        ImproperlyConfigured: If form_fields or confirm_text are not set

    """

    block: str = "action-form"
    tag: str = "form"

    form_fields: list[str] = []  # noqa: RUF012
    confirm_text: str | None = None

    def __init__(
        self,
        form_fields: list[str] | None = None,
        confirm_text: str | None = None,
        **kwargs,
    ):
        self.form_fields = form_fields if form_fields else deepcopy(self.form_fields)
        self.confirm_text = confirm_text if confirm_text else self.confirm_text
        if not self.confirm_text:
            msg = "RowFormButton requires a 'confirm_text' argument or class attribute"
            raise ImproperlyConfigured(msg)
        if not self.form_fields:
            msg = "RowFormButton requires a 'form_fields' argument or class attribute"
            raise ImproperlyConfigured(msg)
        super().__init__(**kwargs)
        # Our superclass added self.text as a block; but that will not work for us,
        # since we want self.text to be the button text, so remove it.
        self.blocks = []
        self._attributes["method"] = "post"

    def get_confirm_text(self, row: Any) -> str:  # noqa: ARG002
        """
        Get the confirmation text for this button.

        Args:
            row: The row data this button is associated with

        Returns:
            str: The confirmation text to display

        """
        return self.confirm_text  # type: ignore[return-value]

    def bind(self, row: Any, table: Any, size: str | None = None) -> RowFormButton:
        """
        Bind this button to a specific row and create a form.

        Creates a complete form with:

        - CSRF token
        - Hidden fields with row data
        - Submit button with confirmation dialog

        Args:
            row: The row data to bind this button to
            table: The table instance that contains this row
            size: Optional size override for the button

        Returns:
            RowFormButton: A configured form button for the specified row

        """
        if not size:
            size = self.size
        action = deepcopy(self)
        action.add_block(
            HiddenInputBlock(input_name="csrfmiddlewaretoken", value=table.csrf_token)
        )
        action._attributes["action"] = self.get_url(row)
        for field in self.form_fields:
            action.add_block(
                HiddenInputBlock(input_name=field, value=getattr(row, field))
            )
        action.add_block(
            InputButton(
                text=self.text,
                color=self.color,
                size=size,
                confirm_text=self.get_confirm_text(row),
            )
        )
        return action


class RowEditButton(RowModelUrlButton):
    """
    A pre-configured button for editing a row's model instance.

    This is a convenience subclass of RowModelUrlButton configured specifically
    for edit operations. It looks for a get_update_url method on the model.

    Either subclass this, setting class attributes to create specific
    model-based buttons, or use it directly with keyword arguments to create
    buttons that link to model-specific URLs.  Note that all keyword
    arguments/class attributes from :py:class:`wildewidgets.Block`  and
    :py:class:`RowModelUrlButton` are also accepted.

    Attributes:
        attribute: The model method to call for URL ("get_update_url").  Your
            model must implement this method or attribute to return the URL for
            editing.
        text: Default button text ("Edit")
        color: Default Bootstrap color ("primary")

    Example:
        Direct usage with keyword arguments:

        .. code-block:: python

            from wildewidgets import RowEditButton

            # Simple usage - requires model.get_update_url() to exist
            button = RowEditButton()

            # Custom text
            button = RowEditButton(text="Modify")

        Subclassing for specific actions:

            class RowCustomEditButton(RowEditButton):
                attribute = "get_custom_update_url"
                text = "Modify"
                color = "warning"
                url_args = ["id"]

    """

    attribute: str = "get_update_url"
    text: str = "Edit"
    color: str = "primary"


class RowDeleteButton(RowFormButton):
    """
    A pre-configured button for deleting a row's model instance.

    This is a convenience subclass of RowFormButton configured specifically
    for delete operations. It submits the row's ID via POST to the URL
    returned by the model's ``get_delete_url`` method by default.

    Either subclass this, setting class attributes to create specific
    model-based buttons, or use it directly with keyword arguments to create
    buttons that link to model-specific URLs.  Note that all keyword
    arguments/class attributes from :py:class:`wildewidgets.Block`  and
    :py:class:`RowModelUrlButton` are also accepted.


    Important:
        Your model must implement a method or attribute named
        :py:attr:`attribute`, which must return the URL to submit the
        form to for deletion.  By default, this is
        :py:attr:`get_delete_url`.

        The form submitted will have by default the following fields:

        - ``csrf_token``: CSRF token for security
        - ``id``: The ID of the row's model instance

        Thus, your delete view should expect a POST request with these fields.

    Note:
        The confirmation text is generated using the row's string
        representation, so ensure your model has a meaningful `__str__` method.
        If you need a custom confirmation message, subclass and override
        :py:meth:`get_confirm_text`.

    Attributes:
        attribute: The model method or attribute to call/access for the URL
            ("get_delete_url")
        text: Default button text ("Delete")
        color: Default Bootstrap color ("outline-secondary")
        form_fields: Default field to submit (["id"])

    Example:
        Direct usage with keyword arguments:

        .. code-block:: python

            from wildewidgets import RowDeleteButton

            # Simple usage - requires model.get_delete_url() to exist
            button = RowDeleteButton()

        Subclassing for specific actions:

            class RowCustomDeleteButton(RowDeleteButton):
                attribute = "get_custom_delete_url"
                text = "Remove"
                color = "danger"
                form_fields = ["id", "name"]  # Submit additional fields

    """

    attribute: str = "get_delete_url"
    text: str = "Delete"
    color: str = "outline-secondary"
    form_fields: list[str] = ["id"]  # noqa: RUF012

    def get_confirm_text(self, row: Any) -> str:
        """
        Generate a confirmation message for deleting this row.

        Creates a message like 'Delete "Item Name"?' using the row's string
        representation.

        Args:
            row: The row data to create a confirmation message for

        Returns:
            str: The confirmation message to display

        """
        return f'Delete "{row!s}"?'


# -------------------------------
# Mixins
# -------------------------------


class ActionsButtonsBySpecMixin:
    """
    A mixin for :py:class:`wildewidgets.DataTable` classes and subclasses that
    adds action buttons based on specifications.

    This mixin allows you to add action buttons to the rightmost column of a
    table by specifying them as tuples that define their behavior. It provides a
    simple way to create standard actions without needing to define button
    classes.

    Actions are specified as tuples with these elements, in this order:

        1. Label (str): The button text
        2. URL name (str): Django URL pattern name, e.g., "app:item-view".  We'll
           reverse this to get the URL.
        3. Method (str, optional): "get" or "post" (default: "get")
        4. Color (str, optional): Bootstrap color class (default: "secondary")
        5. Field name (str, optional): ID field name (default: "id")
        6. JS function (str, optional): JavaScript function to call

    Example:
        .. code-block:: python

            from wildewidgets import ActionsButtonsBySpecMixin

            class MyDataTable(ActionsButtonsBySpecMixin, DataTable):
                actions = [
                    ("View", "app:item-view"),
                    ("Edit", "app:item-edit", "get", "primary"),
                    ("Delete", "app:item-delete", "post", "danger", "id",
                    "confirmDelete")
                ]

        This will add an "Actions" column with buttons for each specified action.
        Each button will be rendered with the appropriate URL and method based on the
        row data.

    Args:
        *args: Positional arguments for the parent class

    Keyword Args:
        actions: List of action specifications to add to the table
        action_button_size: Size of the action buttons (default: "normal")
        default_action_button_label: Default label for the action button
            (default: "View")
        default_action_button_color_class: Default color class for the action button
            (default: "secondary")
        **kwargs: Keyword arguments for the parent class

    """

    #: Per row action buttons.  If not ``False``, this will simply add a
    #: rightmost column  named ``Actions`` with a button named
    #: :py:attr:`default_action_button_label` which when clicked will take the
    #: user to the
    actions: Any = False
    #: How big should each action button be? One of ``normal``, ``btn-lg``, or
    #: ``btn-sm``.
    action_button_size: str = "normal"
    #: The label to use for the default action button
    default_action_button_label: str = "View"
    #: The Bootstrap color class to use for the default action buttons
    default_action_button_color_class: str = "secondary"

    def __init__(
        self,
        *args,
        actions: Any = None,
        action_button_size: str | None = None,
        default_action_button_label: str | None = None,
        default_action_button_color_class: str | None = None,
        **kwargs,
    ):
        self.actions = actions if actions is not None else self.actions
        self.action_button_size = (
            action_button_size if action_button_size else self.action_button_size
        )
        self.default_action_button_label = (
            default_action_button_label
            if default_action_button_label
            else self.default_action_button_label
        )
        self.default_action_button_color_class = (
            default_action_button_color_class
            if default_action_button_color_class
            else self.default_action_button_color_class
        )
        if self.action_button_size != "normal":
            self.action_button_size_class = f"btn-{self.action_button_size}"
        else:
            self.action_button_size_class = ""
        super().__init__(*args, **kwargs)

    def get_template_context_data(self, **kwargs) -> dict[str, Any]:
        """
        Add action column information to the template context.

        Args:
            **kwargs: Keyword arguments to update

        Returns:
            dict: Updated context dictionary with action column information

        """
        if self.actions:
            self.add_column(field="actions", searchable=False, sortable=False)
            kwargs["has_actions"] = True
            kwargs["action_column"] = len(self.column_fields) - 1
        else:
            kwargs["has_actions"] = False
        return super().get_template_context_data(**kwargs)  # type: ignore[misc]

    def get_content(self, **kwargs) -> str:
        """
        Get the rendered content for the table, including action columns.

        Args:
            **kwargs: Keyword arguments for content generation

        Returns:
            str: The HTML content for the table

        """
        if self.actions:
            self.add_column(field="actions", searchable=False, sortable=False)
        return super().get_content(**kwargs)  # type: ignore[misc]

    def get_action_button(
        self,
        row: Any,
        label: str,
        url_name: str,
        method: str = "get",
        color_class: str = "secondary",
        attr: str = "id",
        js_function_name: str | None = None,
    ) -> str:
        """
        Create an action button for a specific row using a Django URL name.

        Args:
            row: The row data this button is for
            label: Text to display on the button
            url_name: Django URL pattern name to link to
            method: HTTP method to use ("get" or "post")
            color_class: Bootstrap color class
            attr: Row attribute to use as ID parameter
            js_function_name: Optional JavaScript function to call on click

        Returns:
            str: HTML for the rendered button

        """
        if url_name:
            base = reverse(url_name)
            # TODO: This assumes we're using QueryStringKwargsMixin, which people
            # outside our group don't use
            url = f"{base}?{attr}={row.id}" if method == "get" else base
        else:
            url = "javascript:void(0)"
        return self.get_action_button_with_url(
            row, label, url, method, color_class, attr, js_function_name
        )

    def get_action_button_url_extra_attributes(self, row: Any) -> str:  # noqa: ARG002
        """
        Get additional URL query parameters for action buttons.

        Override this in subclasses to add custom query parameters.

        Args:
            row: The row data this button is for

        Returns:
            str: Additional URL query parameters

        """
        return ""

    def get_action_button_with_url(
        self,
        row: Any,
        label: str,
        url: str,
        method: str = "get",
        color_class: str = "secondary",
        attr: str = "id",
        js_function_name: str | None = None,
    ) -> str:
        """
        Create an action button for a row with a specific URL.

        Args:
            row: The row data this button is for
            label: Text to display on the button
            url: Complete URL to link to
            method: HTTP method to use ("get" or "post")
            color_class: Bootstrap color class
            attr: Row attribute to use as ID parameter for POST forms
            js_function_name: Optional JavaScript function to call on click

        Returns:
            str: HTML for the rendered button

        """
        url_extra = self.get_action_button_url_extra_attributes(row)
        if url_extra:
            url = f"{url}&{url_extra}"
        if method == "get":
            if js_function_name:
                link_extra = f'onclick="{js_function_name}({row.id});"'
            else:
                link_extra = ""
            return f'<a href="{url}" class="btn btn-{color_class} {self.action_button_size_class} me-2" {link_extra}>{label}</a>'  # noqa: E501
        token_input = f'<input type="hidden" name="csrfmiddlewaretoken" value="{self.csrf_token}">'  # noqa: E501
        id_input = f'<input type="hidden" name="{attr}" value="{row.id}">'
        button = f'<input type=submit value="{label}" class="btn btn-{color_class} {self.action_button_size_class} me-2">'  # noqa: E501
        return f'<form class="form form-inline" action={url} method="post">{token_input}{id_input}{button}</form>'  # noqa: E501

    def get_conditional_action_buttons(self, row: Any) -> str:  # noqa: ARG002
        """
        Get additional action buttons based on row data.

        Override this in subclasses to add buttons conditionally based on
        row attributes.

        Args:
            row: The row data to evaluate

        Returns:
            str: HTML for additional buttons

        """
        return ""

    def render_actions_column(self, row: Any, column: str) -> str:  # noqa: ARG002
        """
        Render all action buttons for a specific row.

        This method generates the complete HTML for the actions column, including:
        1. The default view button if the model has get_absolute_url
        2. All buttons defined in the actions specification
        3. Any conditional buttons from get_conditional_action_buttons

        Args:
            row: The row data to render buttons for
            column: The column name (ignored, always "actions")

        Returns:
            str: Complete HTML for the actions column

        """
        response = '<div class="d-flex flex-row justify-content-end">'
        if hasattr(row, "get_absolute_url"):
            if callable(row.get_absolute_url):
                url = row.get_absolute_url()
            else:
                url = row.get_absolute_url
            view_button = self.get_action_button_with_url(
                row,
                self.default_action_button_label,
                url,
                color_class=self.default_action_button_color_class,
            )
            response += view_button
        if not isinstance(self.actions, bool):
            for action in self.actions:
                if not len(action) > 1:
                    continue
                label = action[0]
                url_name = action[1]
                method = action[2] if len(action) > 2 else "get"  # noqa: PLR2004
                color_class = action[3] if len(action) > 3 else "secondary"  # noqa: PLR2004
                attr = action[4] if len(action) > 4 else "id"  # noqa: PLR2004
                js_function_name = action[5] if len(action) > 5 else ""  # noqa: PLR2004
                response += self.get_action_button(
                    row, label, url_name, method, color_class, attr, js_function_name
                )
        response += self.get_conditional_action_buttons(row)
        response += "</div>"
        return response


class ActionButtonBlockMixin:
    """
    A mixin for :py:class:`wildwidgets.DataTable` classes that adds action
    buttons using :py:class:`RowActionButton` classes.

    This mixin provides a more object-oriented approach to adding action buttons
    compared to :py:class:`ActionsButtonsBySpecMixin`. It uses
    :py:class:`RowActionButton` instances for greater flexibility and
    extensibility.

    Important:
        Typically, you will not use this directly, but rather use
        :py:class:`wildewidgets.StandardActionButtonModelTable` or
        :py:class:`wildewidgets.LookupModelTable`, which already
        has this built in as a mixin.

    Example:
        .. code-block:: python

            from wildewidgets import ActionButtonBlockMixin, DataTable

            class MyTable(ActionButtonBlockMixin, DataTable):
                actions = [
                    RowEditButton(),
                    RowDeleteButton()
                ]
                ...

    Args:
        *args: Positional arguments for the parent class

    Keyword Args:
        actions: List of :py:class:`RowActionButton` instances to add to the
            "Actions" column. If not provided, a default "View" button is used.
        button_size: Size of the action buttons (default: None)
        justify: Justification of the action buttons in the "Actions" column
            (default: "end")

    """

    #: If not ``None``, make all per-row action buttons be this size.
    button_size: str | None = None
    #: The justification of the action buttons in the "Actions" column.
    justify: Literal["start", "center", "end"] = "end"

    #: A list of :py:class:`RowActionButton` subclasses to display in the
    #: "Actions" column.
    actions: list[RowActionButton] = [RowModelUrlButton(text="View", color="secondary")]  # noqa: RUF012

    def __init__(
        self,
        *args,
        actions: list[RowActionButton] | None = None,
        button_size: str | None = None,
        justify: Literal["start", "center", "end"] | None = None,
        **kwargs,
    ):
        self.actions = actions if actions is not None else deepcopy(self.actions)
        self.button_size = button_size if button_size else self.button_size
        self.justify = justify if justify else self.justify
        super().__init__(*args, **kwargs)

    def get_actions(self) -> list[RowActionButton]:
        """
        Get the list of action buttons to display.

        Override this in subclasses to dynamically determine which
        buttons to show.

        Returns:
            list[RowActionButton]: List of action button instances

        """
        return self.actions

    def get_content(self, **kwargs) -> str:
        """
        Get the rendered content for the table, including action columns.

        Args:
            **kwargs: Keyword arguments for content generation

        Returns:
            str: The HTML content for the table

        """
        if self.get_actions():
            self.add_column(field="actions", searchable=False, sortable=False)
        return super().get_content(**kwargs)  # type: ignore[misc]

    def render_actions_column(self, row: Any, column: str) -> str:  # noqa: ARG002
        """
        Render all action buttons for a specific row.

        Creates a horizontal layout containing all visible action buttons
        for the given row.

        Args:
            row: The row data to render buttons for
            column: The column name (ignored, always "actions")

        Returns:
            str: Complete HTML for the actions column

        Note:
            Buttons are only shown if their is_visible method returns True
            for the current user.

        """
        container = HorizontalLayoutBlock(justify=self.justify)
        for action in self.get_actions():
            button = action.bind(row, self, size=self.button_size)
            user = None
            if hasattr(self, "request") and self.request is not None:
                user = self.request.user
            if not button.is_visible(row, user):
                continue
            button.add_class("me-2")
            container.add_block(button)
        button.remove_class("me-2")
        return str(container)


class StandardModelActionButtonBlockMixin(ActionButtonBlockMixin):
    """
    A ready-to-use mixin providing standard "Edit" and "Delete" buttons for
    model tables.

    This mixin provides a convenient configuration of
    :py:class:`ActionButtonBlockMixin` with "Edit" and "Delete" buttons
    pre-configured. It's a quick way to add these common actions to any
    DataTable.

    Note:
        This is used by :py:class:`wildewidgets.LookupModelTable`.

    Requirements:
        - Your model must implement ``get_absolute_url``, ``get_update_url`` and
          ``get_delete_url`` methods

    Example:
        .. code-block:: python

            from wildewidgets import StandardModelActionButtonBlockMixin, DataTable
            from myapp.models import MyModel

            class MyTable(StandardModelActionButtonBlockMixin, DataTable):
                model = MyModel
                fields = ["name", "description"]
                # No additional configuration needed for basic edit/delete buttons

    """

    actions: list[RowActionButton] = [  # noqa: RUF012
        RowModelUrlButton(text="Edit", color="primary", attribute="get_update_url"),
        # TODO: change this to RowFormButton
        RowModelUrlButton(
            text="delete", color="outline-secondary", attribute="get_delete_url"
        ),
    ]
