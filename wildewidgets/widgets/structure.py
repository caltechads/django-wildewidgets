#!/usr/bin/env python
# -*- coding: utf-8 -*-
from copy import deepcopy
import random
from typing import Any, Dict, List, Optional, Type, Tuple, Union
from urllib.parse import urlencode

from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import InvalidPage, Paginator
from django.db.models import QuerySet, Model
from django.http import Http404

from .base import Block, Widget
from .text import HTMLWidget
from .buttons import FormButton
from .headers import BasicHeader, CardHeader


class TabbedWidget(Block):
    """
    This class implements a `Tabler Tabbed Card <https://preview.tabler.io/docs/cards.html>`_.

    Example:

        >>> tab = TabbedWidget()
        >>> tab.add_tab('My First Widget', widget1)
        >>> tab.add_tab('My Second Widget', widget2)
    """

    template_name: str = 'wildewidgets/tab_block.html'
    block: str = 'card'

    slug_suffix: Optional[str] = None
    overflow: str = "auto"

    def __init__(
        self,
        *blocks,
        slug_suffix: str = None,
        overflow: str = None,
        **kwargs
    ):
        self.slug_suffix = slug_suffix if slug_suffix else self.slug_suffix
        self.overflow = overflow if overflow else self.overflow
        super().__init__(*blocks, **kwargs)
        if "style" in self._attributes:
            self._attributes['style'] += f" overflow: {self.overflow};"
        else:
            self._attributes['style'] = f"overflow: {self.overflow};"
        self.tabs = []

    def add_tab(self, name: str, widget: Block) -> None:
        """
        Add a Bootstrap 5 tab named `name` that displays `widget`.

        Args:
            name: the name of the tab
            widget: the block to display in this tab
        """
        self.tabs.append((name, widget))

    def get_context_data(self, *args, **kwargs):
        kwargs['tabs'] = self.tabs
        if not self.slug_suffix:
            self.slug_suffix = random.randrange(0, 10000)
        kwargs['identifier'] = self.slug_suffix
        # kwargs['overflow'] = self.overflow
        return super().get_context_data(*args, **kwargs)


class CardWidget(Block):
    """
    Renders a `Bootstrap 5 Card <https://getbootstrap.com/docs/5.2/components/card/>`_.

    Keyword Args:
        header: A header widget to display above the card.
        header_text: Text used to build a header widget is one is not provided
        card_title: Card title
        card_subtitle: Card subtitle
        widget: Widget to display in card body
        widget_css: CSS to apply to the widget displayed in the card body
        css_class: CSS to apply to the card itself in addition to the defaults
        overflow:
    """
    template_name: str = 'wildewidgets/card_block.html'

    block: str = 'card'

    header: Optional[BasicHeader] = None
    header_text: Optional[str] = None
    header_css: Optional[str] = None
    card_title: Optional[str] = None
    card_subtitle: Optional[str] = None
    widget: Optional[Widget] = None
    widget_css: Optional[str] = None
    overflow: str = "auto"

    def __init__(
        self,
        *blocks,
        header: BasicHeader = None,
        header_text: str = None,
        header_css: str = None,
        card_title: str = None,
        card_subtitle: str = None,
        widget: Widget = None,
        widget_css: str = None,
        overflow: str = None,
        **kwargs
    ):
        self.header = header if header else deepcopy(self.header)
        self.header_text = header_text if header_text else self.header_text
        self.header_css = header_css if header_css else self.header_css
        if self.header_text and not self.header:
            self.header = CardHeader(header_text=self.header_text)
        self.card_title = card_title if card_title else self.card_title
        self.card_subtitle = card_subtitle if card_subtitle else self.card_subtitle
        self.widget = widget if widget else deepcopy(self.widget)
        self.overflow = overflow if overflow else self.overflow
        self.widget_css = widget_css if widget_css else self.widget_css
        super().__init__(*blocks, **kwargs)
        if "style" in self._attributes:
            self._attributes['style'] += f" overflow: {self.overflow};"
        else:
            self._attributes['style'] = f"overflow: {self.overflow};"

    def get_context_data(self, *args, **kwargs):
        kwargs = super().get_context_data(*args, **kwargs)
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
    """
    Base class for :py:class:`PagedModelWidget` and :py:class:`ListModelWidget`.

    Keyword Args:
        model: if this is defined, do ``self.model.objects.all()`` to get our list
            of instances.  Define either this or :py:attr:`queryset`, but not both.
        queryset: use this queryset to get our list of instances.  Define either this or
            :py:attr:`model`, but not both.
        ordering: the ordering to use for the queryset.  This will be applied to both
            :py:attr:`model` and :py:attr:`queryset`
        model_widget: use this widget class to render each model instance.
        model_kwargs: When instantiating :py:attr:`model_widget`, pass this dict into
            the widget constructor as the keyword arguments
        item_label: The label to use for each instance.  This is used in the confirmation
            dialog when deleting instances.

    """
    #: If this is defined, do ``self.model.objects.all()`` to get our list of instances.
    #: Define either this or :py:attr:`queryset`, but not both.
    model: Type[Model] = None
    #: Use this queryset to get our list of instances.  Define either this or
    #: :py:attr:`model`, but not both.
    queryset: QuerySet = None
    #: The ordering to use for the queryset.  This will be applied to both
    #: :py:attr:`model` and :py:attr:`queryset`
    ordering: Union[str, Tuple[str, ...]] = None

    #: Use this widget class to render each model instance.
    model_widget: Type[Widget] = None
    #: When instantiating :py:attr:`model_widget`, pass this dict into the widget constructor
    #: as the keyword arguments
    model_kwargs: Dict[str, Any] = {}

    #: The label to use for each instance.  This is used in the confirmation
    #: dialog when deleting instances.
    item_label: str = "item"

    def __init__(
        self,
        *blocks,
        model: Type[Model] = None,
        queryset: QuerySet = None,
        ordering: str = None,
        model_widget: Widget = None,
        model_kwargs: Dict[str, Any] = None,
        item_label: str = None,
        **kwargs
    ) -> None:
        self.model = model if model else self.model
        self.model_widget = model_widget if model_widget else deepcopy(self.model_widget)
        self.model_kwargs = model_kwargs if model_kwargs else deepcopy(self.model_kwargs)
        self.queryset = queryset if queryset is not None else self.queryset
        self.ordering = ordering if ordering else self.ordering
        self.item_label = item_label if item_label else self.item_label
        super().__init__(*blocks, **kwargs)

    def get_item_label(self, instance: Model) -> str:
        """
        Returns the type of the item displayed. This is used in the confirmation
        dialog when deleting.
        """
        return self.item_label

    def get_model_widget(self, object: Model, **kwargs) -> Widget:
        """
        Returns the individual widget to display as part of the list.

        Args:
            object: the model instance to pass into the model specific widget
        """
        # FIXME: we should not be using ``object`` as a variable -- it is a built-in
        if self.model_widget:
            return self.model_widget(object=object, **kwargs)
        else:
            raise ImproperlyConfigured(
                "%(cls)s is missing a model widget. Define "
                "%(cls)s.model_widget or override "
                "%(cls)s.get_model_widget()." % {'cls': self.__class__.__name__}
            )

    def get_model_widgets(self, instances: List[Model]) -> List[Widget]:
        return [
            self.get_model_widget(object=instance, **self.model_kwargs)
            for instance in instances
        ]

    def get_queryset(self) -> Union[List[Model], QuerySet]:
        """
        Return the list of items for this widget.

        The return value must be an iterable and may be an instance of
        :py:class:`QuerySet` in which case query set specific behavior will be
        enabled.
        """
        if self.queryset is not None:
            queryset = self.queryset
            if isinstance(queryset, QuerySet):
                queryset = queryset.all()
        elif self.model is not None:
            # FIXME: why are we using _default_manager here instead of .objects ?
            # The class may have replaced .objects with a more targeted manager and
            # we won't get that if we always hit _default_manager
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
    A widget that displays a pageable list of widgets
    defined by a queryset. A model or queryset must be provided, and either a model_widget
    or the funtion `get_model_widget` must be provided.

    Args:
        page_kwarg (str, optional): get argument for the page number. Defaults to `page`.
        paginate_by (int, optional): number of widgets per page. Defaults to all widgets.
        extra_url (dict, optional): extra paramters passed in the page links.

    Example::

        >>> widget = PagedModelWidget(
            queryset=mymodel.myobject_set.all(),
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
    template_name: str = 'wildewidgets/paged_model_widget.html'
    block: str = "wildewidgets-paged-model-widget"

    page_kwarg: str = 'page'
    paginate_by: int = 25
    max_page_controls: int = 5

    def __init__(
        self,
        *blocks,
        page_kwarg: str = None,
        paginate_by: int = None,
        extra_url: Dict[str, Any] = None,
        **kwargs
    ):
        self.page_kwarg = page_kwarg if page_kwarg else self.page_kwarg
        self.paginate_by = paginate_by if paginate_by else self.paginate_by
        self.extra_url = extra_url if extra_url else {}
        super().__init__(*blocks, **kwargs)

    def get_context_data(self, *args, **kwargs):
        kwargs = super().get_context_data(*args, **kwargs)
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
            except InvalidPage as e:
                raise Http404(
                    'Invalid page (%(page_number)s): %(message)s' % {
                        'page_number': page_number,
                        'message': str(e)
                    }
                )
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
            kwargs['page_range'] = range(range_start, range_start + pages)
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


class CollapseWidget(Block):
    """
    A `Boostrap Collapse widget <https://getbootstrap.com/docs/5.2/components/collapse/>`_.

    It is typically used in conjunction with a :py:class:`CollapseButton`. Pressing the
    :py:class:`CollapseButton` toggles the visibility of the widget.

    Example:

        >>> collapse_id = 'my-collapse-id'
        >>> collapse = CollapseWidget(
            CrispyFormWidget(form=form),
            css_id=collapse_id,
            css_class="pt-3",
        )
        >>> header = CardHeader(header_text="Services")
        >>> header.add_collapse_button(
            text="Manage",
            color="primary",
            target=f"#{collapse_id}",
        )

    Keyword Args:
        css_id: This ID will be shared with the :py:class:`CollapseButton`.

    """
    block: str = "collapse"


class HorizontalLayoutBlock(Block):
    """
    A container widget intended to display several other widgets aligned horizontally.

    Example:

        >>> layout = HorizontalLayoutBlock(
            LabelBlock(label),
            block1,
            block2,
            justify="end",
            css_class="mt-3",
        )

    Keyword Args:
        align: how to align items veritcally within this widget.  Valid choices: ``start``,
            ``center``, ``end``, ``baselin``, ``stretch``.  See `Bootstrap: Flex,
            justify content <https://getbootstrap.com/docs/5.2/utilities/flex/#align-items>`_.
            If not supplied here and :py:attr:`align` is ``None``, do whatever vertical aligment
            Bootstrap does by default.
        justify: how to align items horizontally within this widget.  Valid choices: ``start``,
            ``center``, ``end``, ``between``, ``around``, ``evenly``.  See `Bootstrap: Flex,
            justify content <https://getbootstrap.com/docs/5.2/utilities/flex/#justify-content>`_.
            If not supplied here and :py:attr:`justify` is ``None``, do whatever horizontal aligment
            Bootstrap does by default.
        flex_size: the Boostrap viewport size below which this will be a vertical list instead
            of a horizontal one.

    """

    #: The valid column content ``justify-content-`` values
    VALID_JUSTIFICATIONS: List[str] = [
        'start',
        'center',
        'end',
        'between',
        'around',
        'evenly'
    ]
    #: The valid column content ``justify-content-`` values
    VALID_ALIGNMENTS: List[str] = [
        'start',
        'center',
        'end',
        'baseline',
        'stretch',
    ]

    #: How to align items veritcally within this widget.  Valid choices: ``start``,
    #: ``center``, ``end``, ``baselin``, ``stretch``.  See `Bootstrap: Flex,
    #: justify content <https://getbootstrap.com/docs/5.2/utilities/flex/#align-items>`_.
    #: If not supplied here and :py:attr:`align` is ``None``, do whatever vertical aligment
    #: Bootstrap does by default.
    align: str = "center"
    #: How to align items horizontally within this widget.  Valid choices: ``start``,
    #: ``center``, ``end``, ``between``, ``around``, ``evenly``.  See `Bootstrap: Flex,
    #: justify content <https://getbootstrap.com/docs/5.2/utilities/flex/#justify-content>`_.
    #: If not supplied here and :py:attr:`justify` is ``None``, do whatever horizontal aligment
    #: Bootstrap does by default.
    justify: str = "between"
    #: the Boostrap viewport size below which this will be a vertical list instead
    #: of a horizontal one.
    flex_size: Optional[str] = None

    def __init__(
        self,
        *blocks,
        align: str = None,
        justify: str = None,
        flex_size: str = None,
        **kwargs
    ):
        self.align = align if align else self.align
        self.justify = justify if justify else self.justify
        self.flex_size = flex_size if flex_size else self.flex_size
        if self.align not in self.VALID_ALIGNMENTS:
            raise ValueError(
                f'"{self.align}" is not a valid vertical alignment value.  Valid values '
                f'are {", ".join(self.VALID_ALIGNMENTS)}'
            )
        if self.justify not in self.VALID_JUSTIFICATIONS:
            raise ValueError(
                f'"{self.justify}" is not a valid horizontal alignment value.  Valid values '
                f'are {", ".join(self.VALID_JUSTIFICATIONS)}'
            )
        super().__init__(*blocks, **kwargs)
        if self.flex_size:
            flex = f"d-{self.flex_size}-flex"
        else:
            flex = "d-flex"
        self.add_class(flex)
        self.add_class(f'align-items-{self.align}')
        self.add_class(f'justify-content-{self.justify}')


class ListModelWidget(MultipleModelWidget):
    """
    This class provides a list of objects defined by a :py:class:`QuerySet`,
    displayed in a "``list-group``" ``<ul>`` block. By default, a widget will be
    provided that simply displays whatever returns from the conversion of the
    object to a ``str``. If a :py:attr:`remove_url` is provided, an `X` icon to
    the right of each object will act as a button to remove the item.

    Example:

        >>> widget = ListModelWidget(
            queryset=myparent.children,
            item_label='child',
            remove_url=reverse('remove_url') + "?id={}",
        )

    Args:
        remove_url: The url to "POST" to in order to delete or remove the object.

    """
    block: str = 'list-group'
    name: str = 'wildewidgets-list-model-widget'
    tag: str = 'ul'
    show_no_items: bool = True

    #: The url to "POST" to in order to delete or remove the object.
    remove_url: Optional[str] = None

    def __init__(self, *args, remove_url=None, **kwargs):
        self.remove_url = remove_url if remove_url else self.remove_url
        super().__init__(*args, **kwargs)
        widgets = self.get_model_widgets(self.get_queryset().all())
        if not widgets and self.show_no_items:
            self.add_block(
                Block(
                    f"No {self.item_label}s",
                    tag='li',
                    name='list-group-item',
                    css_class="fw-light fst-italic border"
                )
            )
        for widget in widgets:
            self.add_block(widget)

    def get_remove_url(self, instance: Model) -> str:
        if self.remove_url:
            return self.remove_url.format(instance.id)
        return ""

    def get_confirm_text(self, instance: Model) -> str:
        item_label = self.get_item_label(instance)
        return f"Are you sure you want to remove this {item_label}?"

    def get_object_text(self, instance: Model) -> str:
        return str(instance)

    def get_model_subblock(self, instance: Model):
        if hasattr(instance, 'get_absolute_url'):
            url = instance.get_absolute_url()
            # FIXME: use a Link here
            return Block(HTMLWidget(
                html=f'<a href="{url}"><label>{self.get_object_text(instance)}</label></a>')
            )
        else:
            return Block(self.get_object_text(instance), tag='label')

    def get_model_widget(self, object: Model = None, **kwargs):
        if self.model_widget:
            return super().get_model_widget(object=object, **kwargs)
        widget = HorizontalLayoutBlock(tag='li', name='list-group-item listmodelwidget__item')
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


class ListModelCardWidget(CardWidget):
    """
    This class provides a :py:class:`CardWidget` with a header and a list of
    objects defined by a :py:class:`QuerySet`, displayed in a
    :py:class:`ListModelWidget`. A filter input is provided to filter the list
    of objects.

    Example:

        >>> widget = ListModelCardWidget(
            queryset = Author.objects.all()[:10]
        )

    Keyword Args:
        list_model_widget_class: The class to use for the list model widget.
            The default is :py:class:`ListModelWidget`.
        list_model_header_class: The class to use for the header.
    """
    SCRIPT: str = """
var filter_input = document.getElementById("{filter_id}");
filter_input.onkeyup = function(e) {{
    var filter = filter_input.value.toLowerCase();
    document.querySelectorAll("{query} label").forEach(label => {{
        var test_string = label.innerText.toLowerCase();
        if (test_string.includes(filter)) {{
            label.closest('.listmodelwidget__item').classList.remove('d-none');
        }}
        else {{
            label.closest('.listmodelwidget__item').classList.add('d-none');
        }}
    }});
    let children = document.querySelectorAll("{query} li");
    for (let i=0; i < children.length; i++) {{
        let child = children[i];
        child.classList.remove('border-top');
    }};
    for (let i=0; i < children.length; i++) {{
        let child = children[i];
        if (child.classList.contains('d-none')) {{
        }}
        else {{
            child.classList.add('border-top');
            break;
        }}
    }};
}};

"""

    list_model_widget_class: Type[Widget] = ListModelWidget
    list_model_header_class: Type[Widget] = None

    def __init__(
        self,
        *args,
        list_model_widget_class: Type[Widget] = None,
        list_model_header_class: Type[Widget] = None,
        **kwargs
    ):
        self.id_base = f"list_modal_card_{random.randrange(0, 1000)}"
        self.list_model_widget_id = f"{self.id_base}_list_model_widget"
        self.filter_id = f"{self.id_base}_filter"
        self.list_model_widget_class = (
            list_model_widget_class if list_model_widget_class else self.list_model_widget_class
        )
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
        filter_label_query = f"#{self.list_model_widget_id}"
        kwargs['script'] = self.SCRIPT.format(
            query=filter_label_query,
            filter_id=self.filter_id
        )
        super().__init__(*args, **kwargs)

    def get_list_model_widget(self, *args, **kwargs):
        return self.list_model_widget_class(*args, **kwargs)

    def get_list_model_header(self, *args, **kwargs):
        from .forms import InputBlock, LabelBlock
        if self.list_model_header_class:
            return self.list_model_header_class(*args, **kwargs)  # pylint: disable=not-callable
        
        # should we just be using a CardHeader here?
        # header = CardHeader(
        #     Block(
        #         LabelBlock(
        #             f'Filter {self.widget.item_label}s',
        #             css_class="d-none",
        #             for_input=self.filter_id
        #         ),
        #         InputBlock(
        #             attributes={
        #                 'type': 'text',
        #                 'placeholder': f'Filter {self.widget.item_label}s',
        #             },
        #             css_id=f'{self.id_base}_filter',
        #             css_class='form-control',
        #         ),
        #         css_class='w-25',
        #     ),
        #     header_text=kwargs.get('title', ""),
        #     css_class="my-1"
        # )
        header = Block(
            Block(
                LabelBlock(
                    f'Filter {self.widget.item_label}s',
                    css_class="d-none",
                    for_input=self.filter_id
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
