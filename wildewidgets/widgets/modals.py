from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.core.exceptions import ImproperlyConfigured

from .base import Block
from .forms import CrispyFormWidget

if TYPE_CHECKING:
    from django.forms import Form


class ModalWidget(Block):
    """
    Renders a Bootstrap 5 Modal dialog.

    This widget creates a Bootstrap modal dialog with a header, body, and footer.
    The modal can be triggered by a button or link with a data-target attribute
    matching the modal's ID.

    Example:
        .. code-block:: python

            from wildewidgets import ModalWidget, Block

            # Create a simple modal
            modal = ModalWidget(
                modal_id="example-modal",
                modal_title="Important Information",
                modal_body=Block("This is the modal content"),
                modal_size="lg"
            )

    Attributes:
        template_name: Path to the template for rendering the modal
        modal_id: Unique identifier for the modal (used in triggering elements)
        modal_title: Text to display in the modal header
        modal_body: Content to display in the modal body (typically a Block)
        modal_size: Size of the modal dialog (None, 'sm', 'lg', or 'xl')

    Keyword Args:
        modal_id: The CSS ID of the modal
        modal_title: The title of the modal
        modal_body: The body of the modal, any Block
        modal_size: The size of the modal (None, 'sm', 'lg', or 'xl')
        **kwargs: Additional attributes passed to the parent Block class

    """

    template_name: str = "wildewidgets/modal.html"
    modal_id: str | None = None
    modal_title: str | None = None
    modal_body: str | None = None
    modal_size: str | None = None

    def __init__(
        self,
        modal_id: str | None = None,
        modal_title: str | None = None,
        modal_body: str | None = None,
        modal_size: str | None = None,
        **kwargs: Any,
    ):
        self.modal_id = modal_id if modal_id else self.modal_id
        self.modal_title = modal_title if modal_title else self.modal_title
        self.modal_body = modal_body if modal_body else self.modal_body
        self.modal_size = modal_size if modal_size else self.modal_size
        super().__init__(**kwargs)

    def get_context_data(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """
        Prepare the context data for the modal template.

        This method adds the modal-specific attributes to the template context
        to be used in rendering the modal dialog.

        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments

        Returns:
            dict: The updated context dictionary with modal attributes

        """
        kwargs = super().get_context_data(*args, **kwargs)
        kwargs["modal_id"] = self.modal_id
        kwargs["modal_title"] = self.modal_title
        kwargs["modal_body"] = self.modal_body
        kwargs["modal_size"] = self.modal_size
        return kwargs


class CrispyFormModalWidget(ModalWidget):
    """
    A modal dialog containing a Django form rendered with django-crispy-forms.

    This specialized modal automatically places a form in the modal body,
    making it easy to create form dialogs for user input. It handles the
    rendering of the form using the CrispyFormWidget.

    Example:
        .. code-block:: python

            from django import forms
            from wildewidgets import CrispyFormModalWidget

            class ContactForm(forms.Form):
                name = forms.CharField()
                email = forms.EmailField()
                message = forms.CharField(widget=forms.Textarea)

            # Create a modal with the form
            modal = CrispyFormModalWidget(
                modal_id="contact-modal",
                modal_title="Contact Us",
                form_class=ContactForm
            )

    Attributes:
        form_class: The form class to instantiate and render in the modal
        form: An already instantiated form to render in the modal

    Args:
        form: An instantiated form to render in the modal
        form_class: A form class to instantiate and render in the modal
        **kwargs: Additional arguments passed to the parent ModalWidget class
            (modal_id, modal_title, modal_size)

    Raises:
        ImproperlyConfigured: If neither form nor form_class is provided

    """

    form_class: type[Form] | None = None
    form: Form | None = None

    def __init__(
        self,
        form: Form | None = None,
        form_class: type[Form] | None = None,
        **kwargs: Any,
    ):
        if not form:
            form = self.form
        if not form_class:
            form_class = self.form_class

        if form_class:
            modal_form = form_class()
        elif form:
            modal_form = form
        else:
            msg = "Either 'form_class' or 'form' must be set"
            raise ImproperlyConfigured(msg)
        modal_body = CrispyFormWidget(form=modal_form)
        kwargs["modal_body"] = modal_body
        super().__init__(**kwargs)
