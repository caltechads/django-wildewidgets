import random

from django import template
from django.urls import reverse_lazy

from wildewidgets.views import WidgetInitKwargsMixin


class BasicMenu(WidgetInitKwargsMixin):
    template_file = "wildewidgets/menu.html"
    navbar_classes = "navbar-expand-lg navbar-light"
    container = "container-lg"
    brand_image = None
    brand_image_width = "100%"
    brand_text = None
    brand_url = "#"
    items = []

    def __init__(self, *args, **kwargs):
        self.menu = {}
        self.active = None
        if args:
            self.active_hierarchy = args[0].split('/')
        else:
            self.active_hierarchy

    def build_menu(self):
        if len(self.active_hierarchy) > 0:
            for item in self.items:
                data = {}
                if type(item[1]) == str:
                    data['url'] = reverse_lazy(item[1])
                    data['extra'] = ''
                    data['kind'] = 'item'

                    if len(item) > 2:
                        extra = item[2]
                        if type(extra) == dict:
                            extra_list = []
                            for k, v in extra.items():
                                extra_list.append(f"{k}={v}")
                            extra = f"?{'&'.join(extra_list)}"
                            data['extra'] = extra
                elif type(item[1]) == list:
                    if len(self.active_hierarchy) > 1:
                        submenu_active = self.active_hierarchy[1]
                    else:
                        submenu_active = None
                    data = self.parse_submemu(item[1], submenu_active)

                self.add_menu_item(item[0], data, item[0] == self.active_hierarchy[0])

    def add_menu_item(self, title, data, active=False):
        self.menu[title] = data
        if active:
            self.active = title

    def parse_submemu(self, items, submenu_active):
        data = {
            'kind': 'submenu'
        }
        sub_menu_items = []
        for item in items:
            if not type(item) == tuple:
                continue
            if item[0] == 'divider':
                subdata = {
                    'divider': True
                }
            else:
                subdata = {
                    'title': item[0],
                    'url': reverse_lazy(item[1]),
                    'extra': '',
                    'divider': False,
                    'active': item[0] == submenu_active,
                }

            if len(item) > 2:
                subdata['extra'] = self.convert_extra(item[2])
            sub_menu_items.append(subdata)

        data['items'] = sub_menu_items
        return data

    def get_content(self, **kwargs):
        self.build_menu()
        context = {
            'menu': self.menu,
            'active': self.active,
            'navbar_classes': self.navbar_classes,
            'navbar_container': self.container,
            'brand_image': self.brand_image,
            'brand_image_width': self.brand_image_width,
            'brand_text': self.brand_text,
            'brand_url': self.brand_url,
            'vertical': "navbar-vertical" in self.navbar_classes,
            'target': random.randrange(0, 10000),
        }
        html_template = template.loader.get_template(self.template_file)
        content = html_template.render(context)
        return content

    def __str__(self):
        return self.get_content()


class DarkMenu(BasicMenu):
    navbar_classes = "navbar-expand-lg navbar-dark bg-secondary"


class VerticalDarkMenu(BasicMenu):
    navbar_classes = "navbar-vertical navbar-expand-lg navbar-dark"


class LightMenu(BasicMenu):
    navbar_classes = "navbar-expand-lg navbar-light"


class MenuMixin:
    menu_class = None
    menu_item = None
    submenu_class = None
    submenu_item = None

    def get_menu_class(self):
        return self.menu_class

    def get_menu_item(self):
        return self.menu_item

    def get_menu(self):
        menu_class = self.get_menu_class()
        if menu_class:
            menu_item = self.get_menu_item()
            return menu_class(menu_item)
        return None

    def get_submenu_class(self):
        return self.submenu_class

    def get_submenu_item(self):
        return self.submenu_item

    def get_submenu(self):
        submenu_class = self.get_submenu_class()
        if submenu_class:
            submenu_item = self.get_submenu_item()
            return submenu_class(submenu_item)
        return None

    def get_context_data(self, **kwargs):
        menu = self.get_menu()
        submenu = self.get_submenu()
        if menu:
            kwargs['menu'] = menu
        if submenu:
            kwargs['submenu'] = submenu
        return super().get_context_data(**kwargs)
