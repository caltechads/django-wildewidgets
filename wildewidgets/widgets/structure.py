from __future__ import annotations

import random
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Final
from urllib.parse import urlencode

from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import InvalidPage, Paginator
from django.http import Http404

from .base import Block, Widget
from .buttons import FormButton
from .headers import BasicHeader, CardHeader
from .text import HTMLWidget

if TYPE_CHECKING:
    from django.db.models import Model, QuerySet


class TabConfig:
    """
    Used to configure the tabs in a :py:class:`PageTabbedWidget`.

    This class holds configuration for an individual tab within a tabbed interface,
    including its name, active state, and optional link.

    Args:
        name: The display name of the tab
        widget: Optional block to display when this tab is active
        active: Whether this tab should be initially active
        link: Optional URL for linking to another page

    Attributes:
        name: The display name of the tab
        active: Whether this tab is active (selected)
        link: URL for the tab if it links to another page

    """

    def __init__(
        self,
        name: str,
        widget: Block | None = None,  # noqa: ARG002
        active: bool = False,
        link: str | None = None,
    ):
        self.name = name
        # TODO: why are we not using widget here?
        # self.widget = widget
        self.active = active
        self.link = link


class PageTabbedWidget(Block):
    """
    Implements a `Tabler Tabbed Card <https://preview.tabler.io/docs/cards.html>`_.

    This widget creates a tabbed interface where the active tab displays a widget,
    and other tabs are links to other pages. When those links are followed, the
    corresponding tab becomes active on the new page. This way, only the active
    widget needs to be rendered.

    Example:
        .. code-block:: python

            from wildewidgets import PageTabbedWidget, TabConfig, Block

            tab = PageTabbedWidget()
            tab.add_link_tab('My First Tab', 'my_first_page_url')
            tab.add_link_tab('My Second Tab', 'my_second_page_url')
            tab.add_active_tab('My Third Tab', widget)

    Args:
        *blocks: Child blocks to include in the tabbed interface

    Keyword Args:
        slug_suffix: Optional suffix for the slug in the URL to differentiate
            between multiple instances of this widget on the same page
        overflow: CSS overflow attribute for the widget (default is "auto")
        **kwargs: Additional keyword arguments passed to the parent class

    """

    #: The Django template to use for rendering this widget.
    template_name: str = "wildewidgets/page_tab_block.html"
    #: The name of the block in the template for CSS styling.
    block: str = "card"
    #: The suffix to use for the slug in the URL.  This is used to
    #: differentiate between multiple instances of this widget on the same page.
    #: This is set to a random number between 0 and 10000 if not provided.
    slug_suffix: str | None = None
    #: The CSS overflow attribute for the widget.
    overflow: str = "auto"

    def __init__(
        self,
        *blocks,
        slug_suffix: str | None = None,
        overflow: str | None = None,
        **kwargs,
    ):
        self.slug_suffix = slug_suffix if slug_suffix else self.slug_suffix
        self.overflow = overflow if overflow else self.overflow
        super().__init__(*blocks, **kwargs)
        if "style" in self._attributes:
            self._attributes["style"] += f" overflow: {self.overflow};"
        else:
            self._attributes["style"] = f"overflow: {self.overflow};"
        self.tabs: list[TabConfig] = []
        self.widget: Block | None = None

    def add_link_tab(self, name: str, url: str) -> None:
        """
        Add a tab that links to another page.

        Creates a tab that, when clicked, navigates to the specified URL.
        This is used for tabs that are not currently active.

        Args:
            name: The display name of the tab
            url: The URL to navigate to when the tab is clicked

        """
        tab = TabConfig(name=name, link=url)
        self.tabs.append(tab)

    def add_active_tab(self, name: str, widget: Block) -> None:
        """
        Add a tab that displays a widget.

        Creates a tab that is initially active and displays the specified widget.

        Args:
            name: The display name of the tab
            widget: The widget to display when this tab is active

        """
        tab = TabConfig(name=name, active=True)
        self.tabs.append(tab)
        self.widget = widget

    def get_context_data(self, *args, **kwargs):
        """
        Prepare the context data for template rendering.

        Adds the tabs, widget, and unique identifier to the template context.

        Args:
            *args: Positional arguments passed to parent method
            **kwargs: Keyword arguments passed to parent method

        Returns:
            dict: The updated context dictionary with tab-specific data

        """
        kwargs["tabs"] = self.tabs
        if not self.slug_suffix:
            self.slug_suffix = random.randrange(0, 10000)  # noqa: S311
        kwargs["identifier"] = self.slug_suffix
        kwargs["widget"] = self.widget
        return super().get_context_data(*args, **kwargs)


class TabbedWidget(Block):
    """
    Implements a `Tabler Tabbed Card <https://preview.tabler.io/docs/cards.html>`_.

    This widget creates a tabbed interface where all tabs are rendered client-side
    (unlike PageTabbedWidget which only renders the active tab). The tabs are switched
    using JavaScript, without page navigation.

    Example:
        .. code-block:: python

            from wildewidgets import TabbedWidget, Block

            widget1 = Block("This is the first widget")
            widget2 = Block("This is the second widget")
            tab = TabbedWidget()
            tab.add_tab('My First Widget', widget1)
            tab.add_tab('My Second Widget', widget2)

    Args:
        *blocks: Child blocks to include in the tabbed interface

    Keyword Args:
        slug_suffix: Optional suffix for the slug in the URL to differentiate
            between multiple instances of this widget on the same page
        overflow: CSS overflow attribute for the widget (default is "auto")
        **kwargs: Additional keyword arguments passed to the parent class

    """

    #: The Django template to use for rendering this widget.
    template_name: str = "wildewidgets/tab_block.html"
    #: The name of the block in the template for CSS styling.
    block: str = "card"

    #: The suffix to use for the slug in the URL.  This is used to
    #: differentiate between multiple instances of this widget on the same page.
    #: If not provided, a random number between 0 and 10000 will be used.
    #: This is used to ensure that the tabs are unique on the page.
    slug_suffix: str | None = None
    #: The CSS overflow attribute for the widget.
    overflow: str = "auto"

    def __init__(
        self,
        *blocks,
        slug_suffix: str | None = None,
        overflow: str | None = None,
        **kwargs,
    ):
        self.slug_suffix = slug_suffix if slug_suffix else self.slug_suffix
        self.overflow = overflow if overflow else self.overflow
        super().__init__(*blocks, **kwargs)
        if "style" in self._attributes:
            self._attributes["style"] += f" overflow: {self.overflow};"
        else:
            self._attributes["style"] = f"overflow: {self.overflow};"
        #: A list of tuples containing the name of the tab and the widget to
        #: display in that tab.  Each tuple is of the form (name, widget), where
        #: `name` is a string and `widget` is a Block.
        self.tabs: list[tuple[str, Block]] = []

    def add_tab(self, name: str, widget: Block) -> None:
        """
        Add a tab to the tabbed interface.

        Creates a tab with the specified name that displays the specified widget
        when the tab is selected.

        Args:
            name: The display name of the tab
            widget: The widget to display when this tab is selected

        """
        self.tabs.append((name, widget))

    def get_context_data(self, *args, **kwargs):
        """
        Prepare the context data for template rendering.

        Adds the tabs and unique identifier to the template context.

        Args:
            *args: Positional arguments passed to parent method
            **kwargs: Keyword arguments passed to parent method

        Returns:
            dict: The updated context dictionary with tab-specific data

        """
        kwargs["tabs"] = self.tabs
        if not self.slug_suffix:
            self.slug_suffix = random.randrange(0, 10000)  # noqa: S311
        kwargs["identifier"] = self.slug_suffix
        # TODO: why is overflow not in kwargs?
        # kwargs['overflow'] = self.overflow
        return super().get_context_data(*args, **kwargs)


class CardWidget(Block):
    """
    Renders a `Bootstrap 5 Card <https://getbootstrap.com/docs/5.2/components/card/>`_.

    This widget creates a Bootstrap card component with optional header, title,
    subtitle, and body content.

    Attributes:
        template_name: The Django template to use for rendering this widget
        block: The name of the block in the template for CSS styling
        header: Optional header widget to display at the top of the card
        header_text: Optional text to use for a simple header (if header is not
            provided)
        header_css: Optional CSS classes to apply to the header
        card_title: Optional title for the card
        card_subtitle: Optional subtitle for the card
        widget: The main widget to display in the card body (required)
        widget_css: Optional CSS classes to apply to the widget
        overflow: CSS overflow attribute for the card

    Example:
        .. code-block:: python

            from wildewidgets import CardWidget, Block

            # Simple card with just a widget
            card = CardWidget(
                widget=Block("Card content"),
                card_title="My Card",
                card_subtitle="Card subtitle"
            )

            # Card with a header and custom widget CSS
            card = CardWidget(
                header_text="Card Header",
                widget=Block("Card content"),
                widget_css="p-4"
            )

    Args:
        *blocks: Child blocks to include in the card body

    Keyword Args:
        header: Optional header widget to display at the top of the card
        header_text: Optional text to use for a simple header (if header is not
            provided)
        header_css: Optional CSS classes to apply to the header
        card_title: Optional title for the card
        card_subtitle: Optional subtitle for the card
        widget: The main widget to display in the card body (required)
        widget_css: Optional CSS classes to apply to the widget
        overflow: CSS overflow attribute for the card

    """

    template_name: str = "wildewidgets/card_block.html"

    block: str = "card"

    header: BasicHeader | None = None
    header_text: str | None = None
    header_css: str | None = None
    card_title: str | None = None
    card_subtitle: str | None = None
    widget: Widget | None = None
    widget_css: str | None = None
    overflow: str = "auto"

    def __init__(
        self,
        *blocks,
        header: BasicHeader | None = None,
        header_text: str | None = None,
        header_css: str | None = None,
        card_title: str | None = None,
        card_subtitle: str | None = None,
        widget: Widget | None = None,
        widget_css: str | None = None,
        overflow: str | None = None,
        **kwargs,
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
            self._attributes["style"] += f" overflow: {self.overflow};"
        else:
            self._attributes["style"] = f"overflow: {self.overflow};"

    def get_context_data(self, *args, **kwargs):
        """
        Prepare the context data for template rendering.

        Adds the card components (header, title, subtitle, widget) to the context.

        Args:
            *args: Positional arguments passed to parent method
            **kwargs: Keyword arguments passed to parent method

        Returns:
            dict: The updated context dictionary with card-specific data

        Raises:
            ImproperlyConfigured: If no widget is defined for the card

        """
        kwargs = super().get_context_data(*args, **kwargs)
        kwargs["header"] = self.header
        kwargs["header_text"] = self.header_text
        kwargs["header_css"] = self.header_css
        kwargs["title"] = self.card_title
        kwargs["subtitle"] = self.card_subtitle
        kwargs["widget"] = self.widget
        kwargs["widget_css"] = self.widget_css
        kwargs["css_class"] = self.css_class

        if not self.widget:
            msg = "You must define a widget."
            raise ImproperlyConfigured(msg)
        return kwargs

    def set_widget(self, widget, css_class=None):
        """
        Set or replace the main widget displayed in the card body.

        Args:
            widget: The widget to display in the card body
            css_class: Optional CSS classes to apply to the widget

        """
        self.widget = widget
        self.widget_css = css_class

    def set_header(self, header):
        """
        Set or replace the header widget displayed at the top of the card.

        Args:
            header: The header widget to display

        """
        self.header = header


class MultipleModelWidget(Block):
    """
    Base class for widgets that display multiple model instances.

    This abstract class provides common functionality for widgets that display
    a list of model instances, such as PagedModelWidget and ListModelWidget.

    Note:
        Either model or queryset must be provided, but not both.

    Example:
        .. code-block:: python

            from wildewidgets import MultipleModelWidget
            from myapp.models import MyModel
            from myapp.widgets import MyModelWidget

            class MyListWidget(MultipleModelWidget):
                model = MyModel
                model_widget = MyModelWidget
                ordering = "-created_at"
                item_label = "item"

    Args:
        *blocks: Child blocks to include in the widget

    Keyword Args:
        model: The Django model class to query for instances
        queryset: A pre-defined queryset to use for fetching model instances
        ordering: The ordering to apply to the queryset (default is None)
        model_widget: The widget class to use for rendering each model instance
        model_kwargs: Optional keyword arguments to pass to the model widget
        item_label: The label to use for each instance (default is "item")

    Raises:
        ImproperlyConfigured: If both model and queryset are defined, or if neither
            is defined, or if model_widget is not defined.

    """

    #: If this is defined, do ``self.model.objects.all()`` to get our list of instances.
    #: Define either this or :py:attr:`queryset`, but not both.
    model: type[Model] | None = None
    #: Use this queryset to get our list of instances.  Define either this or
    #: :py:attr:`model`, but not both.
    queryset: QuerySet | None = None
    #: The ordering to use for the queryset.  This will be applied to both
    #: :py:attr:`model` and :py:attr:`queryset`
    ordering: str | tuple[str, ...] | None = None

    #: Use this widget class to render each model instance.
    model_widget: type[Widget] | None = None
    #: When instantiating :py:attr:`model_widget`, pass this dict into the
    #: widget constructor as the keyword arguments
    model_kwargs: dict[str, Any] = {}  # noqa: RUF012

    #: The label to use for each instance.  This is used in the confirmation
    #: dialog when deleting instances.
    item_label: str = "item"

    def __init__(
        self,
        *blocks,
        model: type[Model] | None = None,
        queryset: QuerySet | None = None,
        ordering: str | None = None,
        model_widget: type[Widget] | None = None,
        model_kwargs: dict[str, Any] | None = None,
        item_label: str | None = None,
        **kwargs,
    ) -> None:
        self.model = model if model else self.model
        self.queryset = queryset if queryset is not None else self.queryset
        if self.model and self.queryset:
            msg = "You must define either model or queryset, but not both."
            raise ImproperlyConfigured(msg)
        self.model_widget = (
            model_widget if model_widget else deepcopy(self.model_widget)
        )
        self.model_kwargs = (
            model_kwargs if model_kwargs else deepcopy(self.model_kwargs)
        )
        self.ordering = ordering if ordering else self.ordering
        self.item_label = item_label if item_label else self.item_label
        super().__init__(*blocks, **kwargs)

    def get_item_label(self, instance: Model) -> str:  # noqa: ARG002
        """
        Get the label to use for a specific model instance.

        This label is used in confirmation dialogs and other UI elements.

        Args:
            instance: The model instance to get the label for

        Returns:
            str: The label for the instance (defaults to the class's item_label)

        """
        # TODO: why is instance an argument here?  It is not used here.
        return self.item_label

    def get_model_widget(self, object: Model, **kwargs) -> Widget:  # noqa: A002
        """
        Create a widget for a specific model instance.

        This method creates and returns a widget for displaying a single model instance.

        Args:
            object: The model instance to create a widget for
            **kwargs: Additional keyword arguments to pass to the widget constructor

        Returns:
            Widget: The widget for displaying the model instance

        Raises:
            ImproperlyConfigured: If model_widget is not defined and this method
                is not overridden

        """
        if self.model_widget:
            return self.model_widget(object=object, **kwargs)
        msg = (
            f"{self.__class__.__name__} is missing a model widget. Define "
            f"{self.__class__.__name__}.model_widget or override "
            f"{self.__class__.__name__}.get_model_widget()."
        )
        raise ImproperlyConfigured(msg)

    def get_model_widgets(self, instances: list[Model]) -> list[Widget]:
        """
        Create widgets for a list of model instances.

        Args:
            instances: List of model instances to create widgets for

        Returns:
            list[Widget]: List of widgets for displaying the model instances

        """
        return [
            self.get_model_widget(object=instance, **self.model_kwargs)
            for instance in instances
        ]

    def get_queryset(self) -> list[Model] | QuerySet:
        """
        Get the queryset of model instances to display.

        This method fetches the model instances to display, either from the
        provided queryset or by querying the model.

        Returns:
            list[Model] | QuerySet: The model instances to display

        Raises:
            ImproperlyConfigured: If neither model nor queryset is defined

        """
        if self.queryset is not None:
            queryset = self.queryset
            queryset = queryset.all()
        elif self.model is not None:
            # TODO: why are we using _default_manager here instead of .objects ?
            # The class may have replaced .objects with a more targeted manager and
            # we won't get that if we always hit _default_manager
            queryset = self.model._default_manager.all()
        else:
            msg = (
                f"{self.__class__.__name__} is missing a QuerySet. Define "
                f"{self.__class__.__name__}.model, {self.__class__.__name__}.queryset, "
                f"or override {self.__class__.__name__}.get_queryset()."
            )
            raise ImproperlyConfigured(msg)
        ordering = self.ordering
        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)
            queryset = queryset.order_by(*ordering)
        return queryset


class PagedModelWidget(MultipleModelWidget):
    """
    A widget that displays a paginated list of model instances.

    This widget creates a paginated list of widgets, with each widget displaying
    a single model instance. It includes pagination controls for navigating
    between pages.

    Example:
        .. code-block:: python

            from wildewidgets import PagedModelWidget, MyObjectWidget

            widget = PagedModelWidget(
                queryset=mymodel.myobject_set.all(),
                paginate_by=10,
                page_kwarg='page',
                model_widget=MyObjectWidget,
                model_kwargs={'foo': 'bar'},
                item_label="object",
                extra_url={
                    'pk': mymodel.id,
                    '#': 'objects',
                },
            )

    Args:
        *blocks: Child blocks to include in the widget

    Keyword Args:
        model: The Django model class to query for instances (optional)
        queryset: A pre-defined queryset to use for fetching model instances
        ordering: The ordering to apply to the queryset (default is None)
        model_widget: The widget class to use for rendering each model instance
        model_kwargs: Optional keyword arguments to pass to the model widget
        item_label: The label to use for each instance (default is "item")
        extra_url: Additional URL parameters to include in pagination links
        page_kwarg: The GET parameter name for the page number (default is "page")
        paginate_by: Number of items per page (default is 25)
        max_page_controls: Maximum number of page controls to display (default is 5)s

    """

    #: The Django template to use for rendering this widget.
    template_name: str = "wildewidgets/paged_model_widget.html"
    #: The name of the block in the template for CSS styling.
    block: str = "wildewidgets-paged-model-widget"

    #: The get argument for the page number. Defaults to `page`.
    page_kwarg: str = "page"
    #: Number of widgets per page. Defaults to all widgets.
    paginate_by: int = 25
    #: Extra parameters passed in the page links.
    max_page_controls: int = 5

    def __init__(
        self,
        *blocks,
        page_kwarg: str | None = None,
        paginate_by: int | None = None,
        extra_url: dict[str, Any] | None = None,
        **kwargs,
    ):
        self.page_kwarg = page_kwarg if page_kwarg else self.page_kwarg
        self.paginate_by = paginate_by if paginate_by else self.paginate_by
        self.extra_url = extra_url if extra_url else {}
        super().__init__(*blocks, **kwargs)

    def get_context_data(self, *args, **kwargs):
        """
        Prepare the context data for template rendering.

        This method:
        1. Handles pagination of the model instances
        2. Creates widgets for the current page of instances
        3. Prepares pagination controls and context
        4. Adds any extra URL parameters for pagination links

        Args:
            *args: Positional arguments passed to parent method
            **kwargs: Keyword arguments passed to parent method

        Returns:
            dict: The updated context dictionary with pagination-specific data

        Raises:
            Http404: If an invalid page number is requested

        """
        kwargs = super().get_context_data(*args, **kwargs)
        self.request = kwargs.get("request")
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
                msg = f"Invalid page ({page_number}): {e!s}"
                raise Http404(msg) from e
            kwargs["widget_list"] = self.get_model_widgets(page.object_list)
            kwargs["page_obj"] = page
            kwargs["is_paginated"] = page.has_other_pages()
            kwargs["paginator"] = paginator
            kwargs["page_kwarg"] = self.page_kwarg
            pages = kwargs["page_obj"].paginator.num_pages
            pages = min(pages, self.max_page_controls)
            page_number = page.number
            max_controls_half = int(self.max_page_controls / 2)
            range_start = max(page_number - max_controls_half, 1)
            kwargs["page_range"] = range(range_start, range_start + pages)
        else:
            kwargs["widget_list"] = self.get_model_widgets(self.get_queryset().all())
        kwargs["item_label"] = self.item_label
        if self.extra_url:
            anchor = self.extra_url.pop("#", None)
            extra_url = f"&{urlencode(self.extra_url)}"
            if anchor:
                extra_url = f"{extra_url}#{anchor}"
            kwargs["extra_url"] = extra_url
        else:
            kwargs["extra_url"] = ""
        return kwargs


class CollapseWidget(Block):
    """
    A `Bootstrap Collapse widget <https://getbootstrap.com/docs/5.2/components/collapse/>`_.

    This widget creates a collapsible content area that can be toggled open or
    closed by a CollapseButton or other trigger element. It's useful for hiding
    content that isn't immediately relevant but might be needed later.

    Note:
        A `CollapseWidget` needs a trigger element (like a
        :py:class:`wildewidgets.CollapseButton`) with the `data-toggle="collapse"`
        attribute and a `data-target` pointing to this widget's ID.

    Example:
        .. code-block:: python

            from wildewidgets import CollapseWidget, CardHeader, CrispyFormWidget

            collapse_id = 'my-collapse-id'
            collapse = CollapseWidget(
                CrispyFormWidget(form=form),
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

    #: The Django template to use for rendering this widget.
    block: str = "collapse"


class HorizontalLayoutBlock(Block):
    """
    A container that aligns child widgets horizontally using flexbox.

    This widget creates a horizontal layout for its child widgets using Bootstrap's
    flexbox utilities. It provides options for controlling vertical and horizontal
    alignment, as well as responsive behavior.

    Example:
        .. code-block:: python

            from wildewidgets import HorizontalLayoutBlock, LabelBlock, Block

            # Create a layout with right-aligned items and centered vertical alignment
            layout = HorizontalLayoutBlock(
                LabelBlock("Label"),
                Block("Content 1"),
                Block("Content 2"),
                justify="end",
                align="center",
                flex_size="md",  # Stack vertically on screens smaller than medium
                css_class="mt-3"
            )

    Args:
        *blocks: Child blocks to include in the horizontal layout

    Keyword Args:
        align: Vertical alignment of items
        justify: Horizontal alignment of items
        flex_size: Bootstrap viewport size below which items stack vertically
        **kwargs: Additional keyword arguments passed to the parent class

    """

    #: The valid column content ``justify-content-`` values
    VALID_JUSTIFICATIONS: Final[list[str]] = [
        "start",
        "center",
        "end",
        "between",
        "around",
        "evenly",
    ]
    #: The valid column content ``justify-content-`` values
    VALID_ALIGNMENTS: Final[list[str]] = [
        "start",
        "center",
        "end",
        "baseline",
        "stretch",
    ]

    #: How to align items veritcally within this widget.  Valid choices: ``start``,
    #: ``center``, ``end``, ``baselin``, ``stretch``.  See `Bootstrap: Flex,
    #: justify content <https://getbootstrap.com/docs/5.2/utilities/flex/#align-items>`_.
    #: If not supplied here and :py:attr:`align` is ``None``, do whatever
    #: vertical aligment Bootstrap does by default.
    align: str = "center"
    #: How to align items horizontally within this widget.  Valid choices:
    #: ``start``, : ``center``, ``end``, ``between``, ``around``, ``evenly``.  See
    #: `Bootstrap: Flex, justify content
    #: <https://getbootstrap.com/docs/5.2/utilities/flex/#justify-content>`_.
    #: If not supplied here and :py:attr:`justify` is ``None``, do whatever
    #: horizontal aligment Bootstrap does by default.
    justify: str = "between"
    #: the Boostrap viewport size below which this will be a vertical list instead
    #: of a horizontal one.
    flex_size: str | None = None

    def __init__(
        self,
        *blocks,
        align: str | None = None,
        justify: str | None = None,
        flex_size: str | None = None,
        **kwargs,
    ):
        self.align = align if align else self.align
        self.justify = justify if justify else self.justify
        self.flex_size = flex_size if flex_size else self.flex_size
        if self.align not in self.VALID_ALIGNMENTS:
            msg = (
                f'"{self.align}" is not a valid vertical alignment value.  Valid '
                f"values are {', '.join(self.VALID_ALIGNMENTS)}"
            )
            raise ValueError(msg)
        if self.justify not in self.VALID_JUSTIFICATIONS:
            msg = (
                f'"{self.justify}" is not a valid horizontal alignment value.  Valid '
                f"values are {', '.join(self.VALID_JUSTIFICATIONS)}"
            )
            raise ValueError(msg)
        super().__init__(*blocks, **kwargs)
        flex = f"d-{self.flex_size}-flex" if self.flex_size else "d-flex"
        self.add_class(flex)
        self.add_class(f"align-items-{self.align}")
        self.add_class(f"justify-content-{self.justify}")


class ListModelWidget(MultipleModelWidget):
    """
    A widget that displays a list of model instances.

    This widget creates an unordered list of items, with each item displaying a
    single model instance. It can optionally include buttons for removing items.

    Example:
        .. code-block:: python

            from wildewidgets import ListModelWidget
            from django.urls import reverse

            # Create a list with remove buttons
            widget = ListModelWidget(
                queryset=parent.children.all(),
                item_label='child',
                remove_url=reverse('remove_child') + "?id={}",
            )

            # Create a read-only list with custom model widget
            widget = ListModelWidget(
                queryset=Author.objects.all(),
                model_widget=AuthorWidget,
                item_label='author'
            )

    Args:
        *args: Positional arguments passed to parent class

    Keyword Args:
        remove_url: Optional URL format string for removing items (with {}
            placeholder for ID)
        **kwargs: Keyword arguments passed to parent class

    Raises:
        ValueError: If model_widget is not defined and no model instance is provided
        ImproperlyConfigured: If neither model nor queryset is defined

    """

    #: The name of the block in the template for CSS styling.
    block: str = "list-group"
    #: Another name for this widget, used in addition to the block name.
    name: str = "wildewidgets-list-model-widget"
    #: The HTML tag to use for the container
    tag: str = "ul"
    #: If True, show a message when there are no items in the list.
    show_no_items: bool = True

    #: The url to "POST" to in order to delete or remove the object.
    remove_url: str | None = None

    def __init__(self, *args, remove_url: str | None = None, **kwargs: Any) -> None:
        self.remove_url = remove_url if remove_url else self.remove_url
        super().__init__(*args, **kwargs)
        result = self.get_queryset()
        if not isinstance(result, list):
            result = list(result.all())
        widgets = self.get_model_widgets(result)
        if not widgets and self.show_no_items:
            self.add_block(
                Block(
                    f"No {self.item_label}s",
                    tag="li",
                    name="list-group-item",
                    css_class="fw-light fst-italic border",
                )
            )
        for widget in widgets:
            self.add_block(widget)

    def get_remove_url(self, instance: Model) -> str:
        """
        Get the URL for removing a specific model instance.

        Args:
            instance: The model instance to get the remove URL for

        Returns:
            str: The URL for removing the instance, or an empty string if not configured

        """
        if self.remove_url:
            return self.remove_url.format(instance.id)
        return ""

    def get_confirm_text(self, instance: Model) -> str:
        """
        Get the confirmation text for removing a specific model instance.

        This text is used in the confirmation dialog when removing an item.

        Args:
            instance: The model instance to get the confirmation text for

        Returns:
            str: The confirmation text for removing the instance

        """
        item_label = self.get_item_label(instance)
        return f"Are you sure you want to remove this {item_label}?"

    def get_object_text(self, instance: Model) -> str:
        """
        Get the display text for a specific model instance.

        Args:
            instance: The model instance to get the display text for

        Returns:
            str: The display text for the instance (defaults to str(instance))

        """
        return str(instance)

    def get_model_subblock(self, instance: Model):
        """
        Create a block for displaying a model instance.

        If the model instance has a get_absolute_url method, the text will be
        wrapped in a link to that URL.

        Args:
            instance: The model instance to create a block for

        Returns:
            Block: A block for displaying the model instance

        """
        if hasattr(instance, "get_absolute_url"):
            url = instance.get_absolute_url()
            # TODO: use a Link here
            return Block(
                HTMLWidget(
                    html=f'<a href="{url}"><label>{self.get_object_text(instance)}'
                    "</label></a>"
                )
            )
        return Block(self.get_object_text(instance), tag="label")

    def get_model_widget(self, object: Model, **kwargs) -> Widget:  # type: ignore[override]  # noqa: A002
        """
        Create a widget for a specific model instance.

        If model_widget is defined, it uses that. Otherwise, it creates a default
        widget with the instance text and an optional remove button.

        Args:
            object: The model instance to create a widget for

        Keyword Args:
            **kwargs: Additional keyword arguments for the widget

        Returns:
            Widget: The widget for displaying the model instance

        Raises:
            ValueError: If obj is None and model_widget is not defined

        """
        if self.model_widget:
            return super().get_model_widget(object=object, **kwargs)
        if object is None:
            if not self.model_widget:
                msg = (
                    f"{self.__class__.__name__} is missing a model widget. Define "
                    f"{self.__class__.__name__}.model_widget or override "
                    f"{self.__class__.__name__}.get_model_widget()."
                )
                raise ValueError(msg)
            return self.model_widget(**kwargs)
        widget = HorizontalLayoutBlock(
            tag="li", name="list-group-item listmodelwidget__item"
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


class ListModelCardWidget(CardWidget):
    """
    A card widget containing a filterable list of model instances.

    This widget creates a card with a header containing a filter input field
    and a body containing a list of model instances. The filter input allows
    users to filter the list by typing.

    Example:
        .. code-block:: python

            from wildewidgets import ListModelCardWidget
            from myapp.models import Author
            from myapp.widgets import AuthorListWidget

            # Basic usage with default list widget
            widget = ListModelCardWidget(
                queryset=Author.objects.all()[:10]
            )

            # Custom list widget and placeholder
            widget = ListModelCardWidget(
                queryset=Author.objects.all(),
                list_model_widget_class=AuthorListWidget,
                placeholder="Search authors...",
                item_label="author"
            )

    Args:
        *args: Positional arguments passed to parent class

    Keyword Args:
        list_model_widget_class: Optional custom widget class for the list model
        list_model_header_class: Optional custom header widget class
        placeholder: Placeholder text for the filter input field
        **kwargs: Keyword arguments passed to parent class

    """

    #: The script to use for filtering the list of objects.
    SCRIPT: str = """
var filter_input = document.getElementById("{filter_id}");
filter_input.onkeyup = function(e) {{
    var filter = e.target.value.toLowerCase();
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

    #: The Widget subclass to use for the list model widget.
    list_model_widget_class: type[Widget] = ListModelWidget
    #: The Widget subclass to use for the header.
    list_model_header_class: type[Widget] | None = None

    def __init__(
        self,
        *args,
        list_model_widget_class: type[Widget] | None = None,
        list_model_header_class: type[Widget] | None = None,
        placeholder: str | None = None,
        **kwargs,
    ):
        self.id_base = f"list_modal_card_{random.randrange(0, 1000)}"  # noqa: S311
        self.list_model_widget_id = f"{self.id_base}_list_model_widget"
        self.filter_id = f"{self.id_base}_filter"
        self.list_model_widget_class = (
            list_model_widget_class
            if list_model_widget_class
            else self.list_model_widget_class
        )
        self.list_model_header_class = (
            list_model_header_class
            if list_model_header_class
            else self.list_model_header_class
        )
        # Pop the kwargs that are used to build the widget and header.
        # These will be passed to the widget and header constructors.
        widget_kwargs = {
            "remove_url": kwargs.pop("remove_url", None),
            "model": kwargs.pop("model", None),
            "model_widget": kwargs.pop("model_widget", None),
            "ordering": kwargs.pop("ordering", None),
            "queryset": kwargs.pop("queryset", None),
            "model_kwargs": kwargs.pop("model_kwargs", {}),
            "item_label": kwargs.pop("item_label", "item"),
            "css_id": self.list_model_widget_id,
        }
        self.widget: Widget = self.get_list_model_widget(**widget_kwargs)
        self.placeholder = placeholder or f"Filter {self.widget.item_label}s"
        kwargs["widget"] = self.widget
        header_kwargs = {
            "title": kwargs.pop("title", ""),
        }
        kwargs["header"] = self.get_list_model_header(**header_kwargs)
        kwargs["header_css"] = "bg-light"
        filter_label_query = f"#{self.list_model_widget_id}"
        kwargs["script"] = self.SCRIPT.format(
            query=filter_label_query, filter_id=self.filter_id
        )
        super().__init__(*args, **kwargs)

    def get_list_model_widget(self, *args, **kwargs):
        """
        Create the list model widget.

        Args:
            *args: Positional arguments for the list model widget
            **kwargs: Keyword arguments for the list model widget

        Returns:
            Widget: The list model widget instance

        """
        return self.list_model_widget_class(*args, **kwargs)

    def get_list_model_header(self, *args, **kwargs):
        """
        Create the header widget with filter input.

        If list_model_header_class is defined, it uses that. Otherwise, it creates
        a default header with a filter input field.

        Args:
            *args: Positional arguments for the header
            **kwargs: Keyword arguments for the header

        Returns:
            Widget: The header widget instance

        """
        from .forms import InputBlock, LabelBlock

        if self.list_model_header_class:
            return self.list_model_header_class(*args, **kwargs)  # pylint: disable=not-callable
        return Block(
            Block(
                LabelBlock(
                    f"Filter {self.widget.item_label}s",
                    css_class="d-none",
                    for_input=self.filter_id,
                ),
                InputBlock(
                    attributes={
                        "type": "text",
                        "placeholder": self.placeholder,
                    },
                    css_id=f"{self.id_base}_filter",
                    css_class="form-control",
                ),
                css_class="w-25",
            ),
            Block(""),
            css_class="d-flex flex-row-reverse w-100",
        )
