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
    slug_suffix = None

    def __init__(self, *args, **kwargs):
        self.tabs = []

    def add_tab(self, name, widget):
        self.tabs.append((name,widget))

    def get_context_data(self, **kwargs):
        kwargs['tabs'] = self.tabs
        if not self.slug_suffix:
            self.slug_suffix = random.randrange(0,10000)
        kwargs['identifier'] = self.slug_suffix
        return kwargs
 

class LinkButton(TemplateWidget):
    template_name = 'wildewidgets/link_button.html'
    url = None
    text = None
    icon = None
    css_class = None
    button_class = 'btn btn-default'

    def __init__(self, **kwargs):
        self.url = kwargs.get('url', self.url)
        self.text = kwargs.get('text', self.text)
        self.icon = kwargs.get('icon', self.icon)

    def get_context_data(self, **kwargs):
        kwargs['url'] = self.url
        kwargs['text'] = self.text
        kwargs['icon'] = self.icon
        kwargs['css_class'] = self.css_class
        kwargs['button_class'] = self.button_class
        return kwargs


class FormButton(TemplateWidget):
    template_name = 'wildewidgets/form_button.html'
    action = None
    text = None
    icon = None
    css_class = None
    button_class = 'btn btn-default'
    confirm_text = None

    def __init__(self, **kwargs):
        self.action = kwargs.get('action', self.action)
        self.text = kwargs.get('text', self.text)
        self.icon = kwargs.get('icon', self.icon)
        self.confirm_text = kwargs.get('confirm_text', self.confirm_text)
        self.data = kwargs.get('data', {})

    def get_context_data(self, **kwargs):
        kwargs['action'] = self.action
        kwargs['text'] = self.text
        kwargs['icon'] = self.icon
        kwargs['css_class'] = self.css_class
        kwargs['button_class'] = self.button_class
        kwargs['confirm_text'] = self.confirm_text
        kwargs['data'] = self.data
        return kwargs


class BasicHeader(TemplateWidget):
    template_name = 'wildewidgets/header_with_controls.html'
    header_level = 1
    header_type = 'h'
    header_text = None
    css_class = "my-3 w-100"
    css_id = None
    badge_text = None
    badge_class = "warning"

    def __init__(self, **kwargs):
        self.header_level = kwargs.get('header_level', self.header_level)
        self.header_type = kwargs.get('header_type', self.header_type)
        self.header_text = kwargs.get('header_text', self.header_text)
        self.css_class = kwargs.get('css_class', self.css_class)
        self.css_id = kwargs.get('css_id', self.css_id)
        self.badge_text = kwargs.get('badge_text', self.badge_text)
        self.badge_class = kwargs.get('badge_class', self.badge_class)

    def get_context_data(self, **kwargs):
        if self.header_type == 'h':
            kwargs['header_class'] = f"h{self.header_level}"
        elif self.header_type == 'display':
            kwargs['header_class'] = f"display-{self.header_level}"

        kwargs['header_level'] = self.header_level
        kwargs['header_text'] = self.header_text
        kwargs['header_type'] = self.header_type
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


class HeaderWithCollapseButton(BasicHeader):
    template_name = 'wildewidgets/header_with_collapse_button.html'
    collapse_id = None
    button_text = None
    button_class = "primary"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.collapse_id = kwargs.get('collapse_id', self.collapse_id)
        self.button_text = kwargs.get('button_text', self.button_text)
        self.button_class = kwargs.get('button_class', self.button_class)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['collapse_id'] = self.collapse_id
        kwargs['button_text'] = self.button_text
        kwargs['button_class'] = self.button_class
        return kwargs


class HeaderWithModalButton(BasicHeader):
    template_name = 'wildewidgets/header_with_modal_button.html'
    modal_id = None
    button_text = None
    button_class = "primary"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.modal_id = kwargs.get('modal_id', self.modal_id)
        self.button_text = kwargs.get('button_text', self.button_text)
        self.button_class = kwargs.get('button_class', self.button_class)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['modal_id'] = self.modal_id
        kwargs['button_text'] = self.button_text
        kwargs['button_class'] = self.button_class
        return kwargs


class HeaderWithWidget(BasicHeader):
    template_name = 'wildewidgets/header_with_widget.html'

    def __init__(self, **kwargs):
        super().__init__()
        self.widget = kwargs.get('widget', None)

    def set_widget(self, widget):
        self.widget = widget
        print(type(widget))

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['widget'] = self.widget
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
    css_class = None

    def __init__(self, **kwargs):
        self.css_class = kwargs.get('css_class', self.css_class)
        self.widgets = []

    def add_widget(self, widget, css_class=None):
        self.widgets.append((widget, css_class))

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['widgets'] = self.widgets
        kwargs['css_class'] = self.css_class
        return kwargs


class CardWidget(TemplateWidget):
    template_name = 'wildewidgets/card.html'
    header = None
    header_text = None
    title = None
    subtitle = None
    widget = None
    widget_css = None
    css_class = None

    def __init__(self, **kwargs):
        self.header = kwargs.get('header', self.header)
        self.header_text = kwargs.get('header_text', self.header_text)
        self.title = kwargs.get('title', self.title)
        self.subtitle = kwargs.get('subtitle', self.subtitle)
        self.widget = kwargs.get('widget', self.widget)
        self.widget_css = kwargs.get('widget_css', self.widget_css)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['header'] = self.header
        kwargs['header_text'] = self.header_text
        kwargs['title'] = self.title
        kwargs['subtitle'] = self.subtitle
        kwargs['widget'] = self.widget
        kwargs['widget_css'] = self.widget_css
        kwargs['css_class'] = self.css_class

        if not self.widget:
            raise ImproperlyConfigured("You must define a widget.")
        return kwargs

    def set_widget(self, widget, css_class=None):
        self.widget = widget
        self.widget_css = css_class

    def set_header(self, header):
        self.header = header


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


class HTMLWidget(TemplateWidget):
    template_name = 'wildewidgets/html_widget.html'
    html = ""
    css_class = None

    def __init__(self, *args, **kwargs):
        self.html = kwargs.get('html', self.html)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['html'] = self.html
        kwargs['css_class'] = self.css_class
        return kwargs

