import random

try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name
    from pygments.formatters import HtmlFormatter
except ModuleNotFoundError:
    # Only needed if using syntax highlighting
    pass

from django import template
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse_lazy

from .wildewidgets import WidgetInitKwargsMixin


class TemplateWidget():
    template_name = None
    
    def get_content(self, **kwargs):
        if not self.template_name:
            return None
        context = self.get_context_data(**kwargs)
        html_template = template.loader.get_template(self.template_name)
        content = html_template.render(context)
        return content

    def __str__(self):
        return self.get_content()

    def get_context_data(self, **kwargs):
        return kwargs


class TabbedWidget(TemplateWidget):
    template_name = 'wildewidgets/tabbed_widget.html'

    def __init__(self, *args, **kwargs):
        self.tabs = []

    def add_tab(self, name, widget):
        self.tabs.append((name,widget))

    def get_context_data(self, **kwargs):
        kwargs['tabs'] = self.tabs
        kwargs['identifier'] = random.randrange(0,1000)
        return kwargs
 

class BasicHeader(TemplateWidget):
    template_name = 'wildewidgets/header_with_controls.html'
    header_level = 1
    header_type = 'h'
    header_text = None
    css_class = None
    css_id = None
    badge_text = None
    badge_class = "warning"

    def get_context_data(self, **kwargs):
        if self.header_type == 'h':
            kwargs['header_class'] = f"h{self.header_level}"
        elif self.header_type == 'display':
            kwargs['header_class'] = f"display-{self.header_level}"

        kwargs['header_level'] = self.header_level
        kwargs['header_text'] = self.header_text
        kwargs['css_class'] = self.css_class
        kwargs['css_id'] = self.css_id
        kwargs['badge_text'] = self.badge_text
        kwargs['badge_class'] = self.badge_class
        return kwargs


class HeaderWithLinkButton(BasicHeader):
    template_name = 'wildewidgets/header_with_link_button.html'
    url = None
    link_text = None
    button_class = "primary"

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['url'] = self.url
        kwargs['link_text'] = self.link_text
        kwargs['button_class'] = self.button_class
        return kwargs


class HeaderWithFormButton(BasicHeader):
    template_name = 'wildewidgets/header_with_form_button.html'
    url = None
    button_text = None

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['url'] = self.url
        kwargs['button_text'] = self.link_text
        return kwargs


class HeaderWithModalButton(BasicHeader):
    template_name = 'wildewidgets/header_with_modal_button.html'
    modal_id = None
    button_text = None
    button_class = "primary"

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['modal_id'] = self.modal_id
        kwargs['button_text'] = self.button_text
        kwargs['button_class'] = self.button_class
        return kwargs


class ModalWidget(TemplateWidget):
    template_name = 'wildewidgets/modal.html'
    modal_id = None
    modal_title = None

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['modal_id'] = self.modal_id
        kwargs['modal_title'] = self.modal_title
        return kwargs


class CrispyFormModalWidget(ModalWidget):
    template_name = 'wildewidgets/crispy_form_modal.html'
    form_class = None
    form = None

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        if self.form_class:
            kwargs['form'] = self.form_class()
        elif self.form:
            kwargs['form'] = self.form
        else:
            raise ImproperlyConfigured("Either 'form_class' or 'form' must be set")
        return kwargs


class WidgetStream(TemplateWidget):
    template_name = 'wildewidgets/widget_stream.html'

    def __init__(self):
        self.widgets = []

    def add_widget(self, widget, css_class=None):
        self.widgets.append((widget, css_class))

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['widgets'] = self.widgets
        return kwargs


class CardWidget(TemplateWidget):
    template_name = 'wildewidgets/card.html'
    header = None
    header_text = None
    title = None
    subtitle = None
    widget = None
    widget_css = None

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['header'] = self.header
        kwargs['header_text'] = self.header_text
        kwargs['title'] = self.title
        kwargs['subtitle'] = self.subtitle
        kwargs['widget'] = self.widget
        kwargs['widget_css'] = self.widget_css

        if not self.widget:
            raise ImproperlyConfigured("You must define a widget.")
        return kwargs

    def add_widget(self, widget, css_class=None):
        self.widget = widget
        self.widget_css = css_class


class CodeWidget(TemplateWidget):
    template_name = 'wildewidgets/code_widget.html'
    language = None
    code = ""
    Line_numbers = False
    css_class = None

    def __init__(self, *args, **kwargs):        
        if 'code' in kwargs:
            self.code = kwargs['code']
        if 'language' in kwargs:
            self.language = kwargs['language']

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        if not self.language:
            raise ImproperlyConfigured("You must define a language.")
        lexer = get_lexer_by_name(self.language)
        formatter = HtmlFormatter(linenos=self.Line_numbers, cssclass="wildewidgets_highlight")
        kwargs['code'] = highlight(self.code, lexer, formatter)
        kwargs['css_class'] = self.css_class
        return kwargs


class MarkdownWidget(TemplateWidget):
    template_name = 'wildewidgets/markdown_widget.html'
    text = ""
    css_class = None

    def __init__(self, *args, **kwargs):
        if 'text' in kwargs:
            self.text = kwargs['text']

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['text'] = self.text
        kwargs['css_class'] = self.css_class
        return kwargs

