#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .base import TemplateWidget

from django.core.exceptions import ImproperlyConfigured


class ModalWidget(TemplateWidget):
    template_name = 'wildewidgets/modal.html'
    modal_id = None
    modal_title = None

    def __init__(self, **kwargs):
        self.modal_id = kwargs.pop('modal_id', self.modal_id)
        self.modal_title = kwargs.pop('modal_title', self.modal_title)
        super().__init__(**kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['modal_id'] = self.modal_id
        kwargs['modal_title'] = self.modal_title
        return kwargs


class CrispyFormModalWidget(ModalWidget):
    template_name = 'wildewidgets/crispy_form_modal.html'
    form_class = None
    form = None

    def __init__(self, **kwargs):
        self.form_class = kwargs.pop('form_class', self.form_class)
        self.form = kwargs.pop('form', self.form)
        super().__init__(**kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        if self.form_class:
            kwargs['form'] = self.form_class()
        elif self.form:
            kwargs['form'] = self.form
        else:
            raise ImproperlyConfigured("Either 'form_class' or 'form' must be set")
        return kwargs
