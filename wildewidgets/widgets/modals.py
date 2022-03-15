#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wildewidgets.widgets.structure import CrispyFormWidget
from .base import TemplateWidget

from django.core.exceptions import ImproperlyConfigured


class ModalWidget(TemplateWidget):
    template_name = 'wildewidgets/modal.html'
    modal_id = None
    modal_title = None
    modal_body = None
    modal_size = None

    def __init__(self, modal_id=None, modal_title=None, modal_body=None, modal_size=None, **kwargs):
        self.modal_id = modal_id if modal_id else self.modal_id
        self.modal_title = modal_title if modal_title else self.modal_title
        self.modal_body = modal_body if modal_body else self.modal_body
        self.modal_size = modal_size if modal_size else self.modal_size
        super().__init__(**kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['modal_id'] = self.modal_id
        kwargs['modal_title'] = self.modal_title
        kwargs['modal_body'] = self.modal_body
        kwargs['modal_size'] = self.modal_size
        return kwargs


class CrispyFormModalWidget(ModalWidget):
    form_class = None
    form = None

    def __init__(self, form=None, form_class=None, **kwargs):
        if form_class:
            modal_form = form_class()
        elif form:
            modal_form = form
        else:
            raise ImproperlyConfigured("Either 'form_class' or 'form' must be set")
        modal_body = CrispyFormWidget(form=modal_form)
        kwargs['modal_body'] = modal_body
        super().__init__(**kwargs)


