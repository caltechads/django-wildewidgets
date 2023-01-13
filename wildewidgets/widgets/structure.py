#!/usr/bin/env python
# -*- coding: utf-8 -*-
from copy import copy
import random
from urllib.parse import urlencode

from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import InvalidPage, Paginator
from django.db.models import QuerySet
from django.http import Http404

from .base import TemplateWidget, Block, InputBlock
from .text import HTMLWidget, StringBlock, LabelBlock
from .buttons import FormButton
from .headers import CardHeader, HeaderWithWidget

from django.core.exceptions import ImproperlyConfigured


class TabbedWidget(Block):
    """Extends TemplateWidget.
    Render a tabbed interace. 
    
    Example::

        tab = TabbedWidget()
        tab.add_tab('My First Widget', widget1)
        tab.add_tab('My Second Widget', widget2)
    """
    template_name = 'wildewidgets/tab_block.html'
    slug_suffix = None
    overflow = "auto"

    def __init__(self, *args, **kwargs):
        css_class = kwargs.get('css_class', "")
        if css_class:
            kwargs['css_class'] = f"card {css_class}"
        else:
            kwargs['css_class'] = "card"
        attributes = kwargs.get('attributes', {})
        if "style" in attributes:
            attributes['style'] += f" overflow: {self.overflow};"
        else:
            attributes['style'] = f"overflow: {self.overflow};"
        kwargs['attributes'] = attributes
        self.tabs = []
        super().__init__(*args, **kwargs)

    def add_tab(self, name, widget):
        """
        Add a Bootstrap 5 tab named `name` that displays `widget`.

        Args:
            name (str): Tab name/title.
            widget (obj): Widget to display in tab.
        """
        self.tabs.append((name, widget))

    def get_context_data(self, **kwargs):
        kwargs['tabs'] = self.tabs
        if not self.slug_suffix:
            self.slug_suffix = random.randrange(0, 10000)
        kwargs['identifier'] = self.slug_suffix
        # kwargs['overflow'] = self.overflow
        return super().get_context_data(**kwargs)


class CardWidget(Block):
    """Extends TemplateWidget.
    Renders a Bootstrap 5 Card.

    Args:
        header (header widget, optional): A header widget to display above the card.
        header_text (str, optional): Text used to build a header widget is one is not provided
        card_title (str): Card title
        card_subtitle (str): Card subtitle
        widget (obj): Widget to display in card body
        widget_css (str): CSS to apply to the widget displayed in the card body
        css_class (str): CSS to apply to the card itself in addition to the defaults
    """
    template_name = 'wildewidgets/card_block.html'
    header = None
    header_text = None
    header_css = None
    card_title = None
    card_subtitle = None
    widget = None
    widget_css = None
    overflow = "auto"

    def __init__(self, *args, **kwargs):
        self.header = kwargs.pop('header', self.header)
        self.header_text = kwargs.pop('header_text', self.header_text)
        self.header_css = kwargs.pop('header_css', self.header_css)
        if self.header_text and not self.header:
            self.header = CardHeader(header_text=self.header_text)
        self.card_title = kwargs.pop('card_title', self.card_title)
        self.card_subtitle = kwargs.pop('card_subtitle', self.card_subtitle)
        self.widget = kwargs.pop('widget', self.widget)
        self.overflow = kwargs.pop('overflow', self.overflow)
        self.widget_css = kwargs.pop('widget_css', self.widget_css)
        css_class = kwargs.get('css_class', "")
        if css_class:
            kwargs['css_class'] = f"card {css_class}"
        else:
            kwargs['css_class'] = "card"
        attributes = kwargs.get('attributes', {})
        if "style" in attributes:
            attributes['style'] += f" overflow: {self.overflow};"
        else:
            attributes['style'] = f"overflow: {self.overflow};"
        kwargs['attributes'] = attributes
        super().__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['header'] = self.header
        kwargs['header_text'] = self.header_text
        kwargs['header_css'] = self.header_css
        kwargs['title'] = self.card_title
        kwargs['subtitle'] = self.card_subtitle
        kwargs['widget'] = self.widget
        kwargs['widget_css'] = self.widget_css
        kwargs['css_class'] = self.css_class

        if not self.widget:
            raise ImproperlyConfigured("You must define a widget.")
        return kwargs

    def set_widget(self, widget, css_class=None):
        """
        Set the widget displayed in the card body

        Args:
            widget (obj): Widget to display in card body
            css_class (str): CSS to apply to the widget displayed in the card body
        """
        self.widget = widget
        self.widget_css = css_class

    def set_header(self, header):
        """
        Set the header widget to display above the card

        Args:
            header (obj): Header widget to display above the card
        """
        self.header = header


class MultipleModelWidget(Block):
    """Extends Block.
    Base class for `PagedModelWidget` and `ListModelWidget`.

    Args:
        model (str, optional): The model to use for the queryset. The default is `None`.
        model_widget (str, optional): The class to use for the model widget. The default is `None`.
        model_kwargs (str, optional): The kwargs to use for the model widget. 
        ordering (str, optional): The ordering to use for the queryset. The default is `None`.
        queryset (str, optional): The queryset to use for the list model widget. 
        item_label (str, optional): The label to use for the item. The default is `item`.        

    """
    model = None
    model_widget = None
    model_kwargs = {}
    ordering = None
    queryset = None
    item_label="item"

    def __init__(self, *args, item_label="", **kwargs):
        self.model = kwargs.pop('model', self.model)
        self.model_widget = kwargs.pop('model_widget', self.model_widget)
        self.ordering = kwargs.pop('ordering', self.ordering)
        self.queryset = kwargs.pop('queryset', self.queryset)
        self.model_kwargs = kwargs.pop('model_kwargs', copy(self.model_kwargs))
        self.item_label = item_label if item_label else self.item_label
        super().__init__(*args, **kwargs)

    def get_item_label(self, object):
        """
        Returns the type of the item displayed. This is used in the confirmation dialog when deleting.
        """
        return self.item_label

    def get_model_widget(self, object=object, **kwargs):
        """
        Returns the individual widget to display as part of the list.
        """
        if self.model_widget:
            return self.model_widget(object=object, **kwargs)
        else:
            raise ImproperlyConfigured(
                "%(cls)s is missing a model widget. Define "
                "%(cls)s.model_widget or override "
                "%(cls)s.get_model_widget()." % {'cls': self.__class__.__name__}
            )

    def get_model_widgets(self, object_list):
        widgets = []
        for object in object_list:
            widgets.append(self.get_model_widget(object=object, **self.model_kwargs))
        return widgets

    def get_queryset(self):
        """
        Return the list of items for this widget.
        The return value must be an iterable and may be an instance of
        `QuerySet` in which case `QuerySet` specific behavior will be enabled.
        """
        if self.queryset is not None:
            queryset = self.queryset
            if isinstance(queryset, QuerySet):
                queryset = queryset.all()
        elif self.model is not None:
            queryset = self.model._default_manager.all()
        else:
            raise ImproperlyConfigured(
                "%(cls)s is missing a QuerySet. Define "
                "%(cls)s.model, %(cls)s.queryset, or override "
                "%(cls)s.get_queryset()." % {
                    'cls': self.__class__.__name__
                }
            )
        ordering = self.ordering
        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)
            queryset = queryset.order_by(*ordering)
        return queryset


class PagedModelWidget(MultipleModelWidget):
    """
    Extends `MultipleModelWidget`. A widget that displays a pageable list of widgets 
    defined by a queryset. A model or queryset must be provided, and either a model_widget 
    or the funtion `get_model_widget` must be provided.

    Args:
        page_kwarg (str, optional): get argument for the page number. Defaults to `page`.
        paginate_by (int, optional): number of widgets per page. Defaults to all widgets.
        extra_url (dict, optional): extra paramters passed in the page links.

    Example::

        PagedModelWidget(
            queryset=project.myobject_set.all(),
            paginate_by=3,
            page_kwarg='myobject_page',
            model_widget=MyObjectWidget,
            model_kwargs={'foo': bar},
            item_label="myobject",
            extra_url={
                'pk': myobject.id,
                '#':'myobjects',
            },
        )
    """
    template_name = 'wildewidgets/paged_model_widget.html'
    page_kwarg = 'page'
    paginate_by = None
    max_page_controls = 5
    css_class = "wildewidgets-paged-model-widget "

    def __init__(self, *args, **kwargs):
        self.page_kwarg = kwargs.pop('page_kwarg', self.page_kwarg)
        self.paginate_by = kwargs.pop('paginate_by', self.paginate_by)
        self.extra_url = kwargs.pop('extra_url', {})
        super().__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        self.request = kwargs.get('request')
        if self.paginate_by:
            paginator = Paginator(self.get_queryset(), self.paginate_by)
            page_number = self.request.GET.get(self.page_kwarg)
            try:
                page_number = int(page_number)
            except (TypeError, ValueError):
                page_number = 1
            try:
                page = paginator.page(page_number)
                kwargs['widget_list'] = self.get_model_widgets(page.object_list)
                kwargs['page_obj'] = page
                kwargs['is_paginated'] = page.has_other_pages()
                kwargs['paginator'] = paginator
                kwargs['page_kwarg'] = self.page_kwarg
                pages = kwargs['page_obj'].paginator.num_pages
                if pages > self.max_page_controls:
                    pages = self.max_page_controls
                page_number = page.number
                max_controls_half = int(self.max_page_controls / 2)
                range_start = 1 if page_number - max_controls_half < 1 else page_number - max_controls_half
                kwargs['page_range'] = range(range_start, range_start+pages)
            except InvalidPage as e:
                raise Http404(
                    'Invalid page (%(page_number)s): %(message)s' % {
                        'page_number': page_number,
                        'message': str(e)
                    }
                )
        else:
            kwargs['widget_list'] = self.get_model_widgets(self.get_queryset().all())
        kwargs['item_label'] = self.item_label
        if self.extra_url:
            anchor = self.extra_url.pop("#", None)
            extra_url = f"&{urlencode(self.extra_url)}"
            if anchor:
                extra_url = f"{extra_url}#{anchor}"
            kwargs['extra_url'] = extra_url
        else:
            kwargs['extra_url'] = ''
        return kwargs


class CrispyFormWidget(Block):
    """Extends Block.
    A widget that displays a crispy_form widget.

    Args:
        form (obj, optional): A crispy form to display. If none is specified, 
            it will be assumed that `form` is specified elsewhere in the context.
    """
    template_name = 'wildewidgets/crispy_form_widget.html'
    css_class = "wildewidgets-crispy-form-widget"

    def __init__(self, *args, form=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.form = form

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        if self.form:
            kwargs['form'] = self.form
        return kwargs


class CollapseWidget(Block):
    """Extends Block.
    A widget that is initially displayed hidden. It is typically used in conjunction
    with a `CollapseButton`. Pressing the `CollapseButton` toggles the visibility of
    the widget.

    Args:
        css_id (str): This ID will be shared with the `CollapseButton`.

    Example::

        CollapseWidget(
            CrispyFormWidget(
                form=form,
            ),
            css_id=collapse_id,
            css_class="pt-3",
        )
        header = CardHeader(header_text="Services")
        header.add_collapse_button(
            text="Manage",
            color="primary",
            target=f"#{collapse_id}",
        )
    """
    css_class="collapse"

    def __init__(self, *args, **kwargs):
        if "css_class" in kwargs:
            kwargs['css_class'] = f"{kwargs['css_class']} collapse"
        else:
            kwargs['css_class'] = self.css_class
        super().__init__(*args, **kwargs)


class HorizontalLayoutBlock(Block):
    """Extends Block.
    A container widget intended to display several other widgets aligned horizontally.

    Args:
        align (str, optional): Flex alignment as defined in Bootstrap 5 (start, end, center...). 
            Default is `center`.
        justify (str, optional): Flex justification as defined in Bootstrap 5 (start, end, center, between...).
            Default is `between`.
        flex_size (str, optional): Flex size as defined in Bootstrap 5 - sm, md, lg, xl, xxl. Default is None.

    Example::

        HorizontalLayoutBlock(
            LabelBlock(label),
            block1,
            block2,
            justify="end",
            css_class="mt-3",
        )
    """
    align="center"
    justify="between"
    flex_size=None

    def __init__(self, *blocks, **kwargs):
        align = kwargs.pop("align", self.align)
        justify = kwargs.pop("justify", self.justify)
        flex_size = kwargs.pop("flex_size", self.flex_size)
        if flex_size:
            flex = f"d-{flex_size}-flex"
        else:
            flex = "d-flex"
        css_class = kwargs.get("css_class", "")
        css_class += f" {flex} align-items-{align} justify-content-{justify}"
        kwargs["css_class"] = css_class
        super().__init__(*blocks, **kwargs)


class ListModelWidget(MultipleModelWidget):
    """
    Extends `MultipleModelWidget`. This class provides a list of objects
    defined by a QuerySet, displayed in a list-group `ul` block. By default,
    a widget will be provided that simply displays whatever returns from
    the conversion of the object to a `str`. If a `remove_url` is provided,
    an `X` icon to the right of each object will act as a button to remove
    the item.

    Args:
        remove_url (str, optional): The url to `POST` to in order to delete or 
            remove the object. 

    Example::

        widget = ListModelWidget(
            queryset=myparent.children,
            item_label='child',
            remove_url=reverse('remove_url') + "?id={}",
        )
    """
    base_css_class = "wildewidgets-list-model-widget list-group"
    tag='ul'
    remove_url=None

    def __init__(self, *args, remove_url=None, **kwargs):
        self.remove_url = remove_url if remove_url else self.remove_url
        css_class = kwargs.get("css_class", "")
        css_class += f" {self.base_css_class}"
        kwargs["css_class"] = css_class.strip()
        super().__init__(*args, **kwargs)
        self.remove_url = remove_url
        super().__init__(*args, **kwargs)
        widgets = self.get_model_widgets(self.get_queryset().all())
        if not widgets:
            self.add_block(StringBlock(f"No {self.item_label}s", tag='li', css_class="list-group-item fw-light fst-italic border"))
        for widget in widgets:
            self.add_block(widget)

    def get_remove_url(self, object):
        if self.remove_url:
            return self.remove_url.format(object.id)
        return ""

    def get_confirm_text(self, object):
        item_label = self.get_item_label(object)
        return f"Are you sure you want to remove this {item_label}?"

    def get_object_text(self, object):
        return str(object)

    def get_model_subblock(self, object):
        if hasattr(object, 'get_absolute_url'):
            url = object.get_absolute_url()
            return Block(HTMLWidget(html=f'<a href="{url}"><label>{self.get_object_text(object)}</label></a>'))
        else:
            return Block(StringBlock(self.get_object_text(object), tag='label'))

    def get_model_widget(self, object=object, **kwargs):
        if self.model_widget:
            return super().get_model_widget(object=object, **kwargs)
        widget = HorizontalLayoutBlock(
            tag='li',
            css_class='list-group-item'
        )
        widget.add_block(self.get_model_subblock(object))
        remove_url = self.get_remove_url(object)
        if remove_url:
            widget.add_block(
                FormButton(
                    close=True,
                    action=remove_url,
                    confirm_text=self.get_confirm_text(object),
                ),
            )
        return widget


list_model_card_filter_script = """
var filter_input = document.getElementById("{filter_id}");
filter_input.onkeyup = function(e) {{
    var filter=filter_input.value.toLowerCase();
    document.querySelectorAll("{query} label").forEach(label => {{
        var test_string = label.innerText.toLowerCase();
        if (test_string.includes(filter)) {{        
            label.parentElement.parentElement.classList.remove('d-none');
        }}
        else {{
            label.parentElement.parentElement.classList.add('d-none');
        }}        
    }});
    let children = document.querySelectorAll("{query} li");
    for (let i=0;i<children.length;i++) {{
        let child=children[i];
        child.classList.remove('border-top');
    }};
    for (let i=0;i<children.length;i++) {{
        let child=children[i];
        if (child.classList.contains('d-none')) {{            
        }}
        else {{
            child.classList.add('border-top');
            break;
        }}
    }};
}};

"""

class ListModelCardWidget(CardWidget):
    """
    Extends `CardWidget`. This class provides a card with a header and a list of objects
    defined by a QuerySet, displayed in a ListModelWidget. A filter input is provided
    to filter the list of objects.

        Args:
        list_model_widget_class (str, optional): The class to use for the list model widget. 
            The default is `ListModelWidget`.
        list_model_header_class (str, optional): The class to use for the header.
        remove_url (str, optional): The url to `POST` to in order to remove the object.
            The url should contain a `{}` that will be replaced with the object id.
        model (str, optional): The model to use for the queryset. The default is `None`.
        model_widget (str, optional): The class to use for the model widget. The default
            is `HorizontalLayoutBlock`.
        model_kwargs (str, optional): The kwargs to use for the model widget. 
        ordering (str, optional): The ordering to use for the queryset. The default is `None`.
        queryset (str, optional): The queryset to use for the list model widget. 
        item_label (str, optional): The label to use for the item. The default is `item`.
        css_class (str, optional): The css class to add the default classes. 

    Example::

        widget = ListModelCardWidget(
            queryset = Author.objects.all()[:10]
        )

    """
    list_model_widget_class = ListModelWidget
    list_model_header_class = None
    base_css_class = "card"

    def __init__(self, *args, **kwargs):
        self.id_base = f"list_modal_card_{random.randrange(0, 1000)}"
        self.list_model_widget_id = f"{self.id_base}_list_model_widget"
        self.filter_id = f"{self.id_base}_filter"
        self.list_model_widget_class = kwargs.pop("list_model_widget_class", self.list_model_widget_class)
        css_class = kwargs.get("css_class", "")
        css_class += f" {self.base_css_class}"
        kwargs["css_class"] = css_class.strip()
        widget_kwargs = {
            'remove_url': kwargs.pop("remove_url", None),
            'model': kwargs.pop("model", None),
            'model_widget': kwargs.pop("model_widget", None),
            'ordering': kwargs.pop("ordering", None),
            'queryset': kwargs.pop("queryset", None),
            'model_kwargs': kwargs.pop("model_kwargs", {}),
            'item_label': kwargs.pop("item_label", "item"),
            'css_id': self.list_model_widget_id,
        }
        self.widget = self.get_list_model_widget(**widget_kwargs)
        kwargs['widget'] = self.widget
        header_kwargs = {
            'title': kwargs.pop("title", ""),
        }
        kwargs['header'] = self.get_list_model_header(**header_kwargs)
        kwargs['header_css'] = "bg-light"
        print(self.filter_id)
        filter_label_query = f"#{self.list_model_widget_id}"
        kwargs['script'] = list_model_card_filter_script.format(query=filter_label_query, filter_id=self.filter_id)
        super().__init__(*args, **kwargs)        
        
    def get_list_model_widget(self, *args, **kwargs):
        return self.list_model_widget_class(*args, **kwargs)
        
    def get_list_model_header(self, *args, **kwargs):
        if self.list_model_header_class:
            return self.list_model_header_class(*args, **kwargs)
        header = Block(
            Block(
                LabelBlock(
                    f'Filter {self.widget.item_label}s', 
                    css_class="d-none",
                    attributes={
                        'for': self.filter_id,
                    },
                ),
                InputBlock(
                    attributes={
                        'type': 'text',
                        'placeholder': f'Filter {self.widget.item_label}s',
                    },                    
                    css_id=f'{self.id_base}_filter',
                    css_class='form-control',  
                ),
                css_class='w-25',  
            ),
            Block(""),
            css_class="d-flex flex-row-reverse w-100"
        )
        return header
        

