from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.core.exceptions import ImproperlyConfigured

from .base import Block, Widget
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
        self.modal_id = modal_id or self.modal_id
        self.modal_title = modal_title or self.modal_title
        self.modal_body = modal_body or self.modal_body
        self.modal_size = modal_size or self.modal_size
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


class OffcanvasWidget(Block):
    """
    Renders a Bootstrap 5 offcanvas panel.

    The widget renders a header and places the supplied child widget inside the
    offcanvas body.

    Attributes:
        template_name: Path to the template for rendering the offcanvas panel.
        offcanvas_id: Unique identifier used by trigger elements.
        offcanvas_title: Title displayed in the offcanvas header.
        widget: Widget displayed in the offcanvas body.
        placement: Bootstrap offcanvas placement suffix.
        widget_css: Optional CSS classes applied around the body widget.
        scroll: Whether body scrolling is enabled while the offcanvas is open.
        backdrop: Whether the offcanvas backdrop is enabled.

    Keyword Args:
        offcanvas_id: The CSS ID of the offcanvas panel.
        offcanvas_title: The title of the offcanvas panel.
        widget: The widget to display in the offcanvas body.
        placement: Bootstrap offcanvas placement suffix.
        widget_css: Optional CSS classes applied around the body widget.
        scroll: Whether body scrolling is enabled while the offcanvas is open.
        backdrop: Whether the offcanvas backdrop is enabled.
        **kwargs: Additional attributes passed to the parent Block class.

    Raises:
        ImproperlyConfigured: If the id, title, or body widget is missing.

    """

    #: Path to the template for rendering the offcanvas panel.
    template_name: str = "wildewidgets/offcanvas.html"
    #: Unique identifier used by trigger elements.
    offcanvas_id: str | None = None
    #: Title displayed in the offcanvas header.
    offcanvas_title: str | None = None
    #: Widget displayed in the offcanvas body.
    widget: Widget | None = None
    #: Bootstrap offcanvas placement suffix.
    placement: str = "start"
    #: Optional CSS classes applied around the body widget.
    widget_css: str | None = None
    #: Whether body scrolling is enabled while the offcanvas is open.
    scroll: bool = False
    #: Whether the offcanvas backdrop is enabled.
    backdrop: bool = True

    def __init__(
        self,
        offcanvas_id: str | None = None,
        offcanvas_title: str | None = None,
        widget: Widget | None = None,
        placement: str | None = None,
        widget_css: str | None = None,
        scroll: bool | None = None,
        backdrop: bool | None = None,
        **kwargs: Any,
    ):
        #: Unique identifier used by trigger elements.
        self.offcanvas_id = offcanvas_id or self.offcanvas_id
        #: Title displayed in the offcanvas header.
        self.offcanvas_title = offcanvas_title or self.offcanvas_title
        #: Widget displayed in the offcanvas body.
        self.widget = widget or self.widget
        #: Bootstrap offcanvas placement suffix.
        self.placement = placement or self.placement
        #: Optional CSS classes applied around the body widget.
        self.widget_css = widget_css or self.widget_css
        #: Whether body scrolling is enabled while the offcanvas is open.
        self.scroll = self.scroll if scroll is None else scroll
        #: Whether the offcanvas backdrop is enabled.
        self.backdrop = self.backdrop if backdrop is None else backdrop
        super().__init__(**kwargs)
        if not self.offcanvas_id:
            msg = "You must define offcanvas_id."
            raise ImproperlyConfigured(msg)
        if not self.offcanvas_title:
            msg = "You must define offcanvas_title."
            raise ImproperlyConfigured(msg)
        if not self.widget:
            msg = "You must define widget."
            raise ImproperlyConfigured(msg)

    def get_context_data(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """
        Prepare the context data for the offcanvas template.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The updated context dictionary with offcanvas attributes.

        """
        kwargs = super().get_context_data(*args, **kwargs)
        kwargs["offcanvas_id"] = self.offcanvas_id
        kwargs["offcanvas_title"] = self.offcanvas_title
        kwargs["widget"] = self.widget
        kwargs["placement"] = self.placement
        kwargs["widget_css"] = self.widget_css
        kwargs["scroll"] = str(self.scroll).lower()
        kwargs["backdrop"] = str(self.backdrop).lower()
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
