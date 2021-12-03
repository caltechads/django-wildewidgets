*******
Widgets
*******

There are a number of general purpose widgets available, along with some supporting classes.

* BasicMenu
* LightMenu - Often used as a submenu beneath the main menu.
* MenuMixin - Used for view classes that utilize menus.
* TemplateWidget - A generic widget that gives you full control over both the content and the layout.
* TabbedWidget - A widget that contains other widgets in a tabbed interface.
* BasicHeader - A header widget that is a base class for widgets with right justified controls.
* HeaderWithLinkButton - A header widget with a link button on the right.
* HeaderWithModalButton - A header widget with a modal button on the right.
* ModalWidget - A Bootstrap modal dialog widget base class.
* CrispyFormModalWidget - A Boostrap modal dialog containing a crispy form.
* WidgetStream - A container widget that contains a list of child widgets that are displayed sequentially.
* CardWidget - A Bootstrap card widget that displays a child widget in its body.
* CodeWidget - A widget that contains a block of syntax highlighted code.
* MarkdownWidget - A widget that contains a block of rendered markdown text.

Menu
====

A basic menu requires only one class variable defined, `items`::

    class MainMenu(BasicMenu):

        items = [
            ('Users', 'core:home'), 
            ('Uploads','core:uploads'),
        ]

The `items` variable is a list of tuples, where the first element is the menu item text and the second element is the URL name. If the `items` variable is defined dynamically in `__init__`, a third optional element in the tuple is a dictionary of get arguments.

View Mixin
----------

The view mixin `MenuMixin` only requires you to specify the menu class, and the name of the menu item that should be selected::

    class TestView(MenuMixin, TemplateView):
        menu_class = MainMenu
        menu_item = 'Users'
        ...

If several views use the same menu, you can create a subclass::

    class UsersMenuMixin(MenuMixin):
        menu_class = MainMenu
        menu_item = 'Users'

Then the view won't need to define these variables::

    class TestView(UsersMenuMixin, TemplateView):
        ...

Sub Menus
---------

Typically, a `LightMenu`` is used as a submenu, below the main menu. The view class, or menu mixin, then becomes::

    class TestView(MenuMixin, TemplateView):
        menu_class = MainMenu
        menu_item = 'Users'
        submenu_class = SubMenu
        submenu_item = 'Main User Task'
        ...

TemplateWidget
==============

A template widget encapsulates a defined UI element on a page. It consists of data, and the template to display the data::

    class HelloWorldWidget(TemplateWidget):
        template_name = 'core/hello_world.html'

        def get_context_data(self, **kwargs):
            kwargs['data'] = "Hello world"
            return kwargs

TabbedWidget
============

A tabbed widget contains other widgets in a tabbed interface. Tabs are added by called `add_tab` with the name to display on the tab, and the widget to display under that tab. It can be any type of wildewidgets widget::

    class TestTabbedWidget(TabbedWidget):
    
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            widgets = WidgetStream()
            widgets.add_widget(Test1Header())
            widgets.add_widget(Test1Table())
            self.add_tab("Test 1", widgets)

            widgets = WidgetStream()
            widgets.add_widget(Test2Header())
            widgets.add_widget(Test2Table())
            self.add_tab("Test 2", widgets)
    


