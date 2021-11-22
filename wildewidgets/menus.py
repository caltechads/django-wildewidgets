from django import template
from django.urls import reverse_lazy

from .wildewidgets import WidgetInitKwargsMixin


class BasicMenu(WidgetInitKwargsMixin):

    template_file = "wildewidgets/menu.html"
    navbar_classes = "navbar-expand-lg navbar-light"
    container = "container-lg"
    items = []

    def __init__(self, *args, **kwargs):
        self.menu= {}
        self.active = None
        if args:
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
                            for k,v in extra.items():
                                extra_list.append(f"{k}={v}")
                            extra = f"?{'&'.join(extra_list)}"
                            data['extra'] = extra
                elif type(item[1]) == list:
                    data = self.parse_submemu(item[1])

                self.add_menu_item(item[0], data, item[0] == args[0])

    def add_menu_item(self, title, data, active=False):
        self.menu[title] = data
        if active:
            self.active = title

    def parse_submemu(self, items):
        data = {
            'kind':'submenu'            
        }
        sub_menu_items = []
        for item in items:
            if not type(item) == tuple:
                continue
            if item[0] == 'divider':
                subdata = {
                    'divider':True
                }
            else:
                subdata = {                    
                    'title':item[0],
                    'url':reverse_lazy(item[1]),
                    'extra':'',
                    'divider':False
                }

            if len(item) > 2:
                subdata['extra'] = self.convert_extra(item[2])
            sub_menu_items.append(subdata)

        data['items'] = sub_menu_items
        return data

    def get_content(self, **kwargs):
        context = {
            'menu':self.menu, 
            'active':self.active,
            'navbar_classes':self.navbar_classes,
            'navbar_container':self.container,
        }
        html_template = template.loader.get_template(self.template_file)
        content = html_template.render(context)
        return content

    def __str__(self):
        return self.get_content()


class DarkMenu(BasicMenu):
    navbar_classes = "navbar-expand-lg navbar-dark bg-secondary"


class LightMenu(BasicMenu):
    navbar_classes = "navbar-expand-lg navbar-light"


class MenuMixin():
    menu_class = None
    submenu_class = None
    
    def get_menu_class(self):
        if self.menu_class:
            return self.menu_class
        return None
        
    def get_menu(self):
        menu_class = self.get_menu_class()
        if menu_class:
            menu_item = None
            if self.menu_item:
                menu_item = self.menu_item
            return menu_class(self.menu_item)
        return None
        
    def get_submenu_class(self):
        if self.submenu_class:
            return self.submenu_class
        return None
        
    def get_submenu(self):
        submenu_class = self.get_submenu_class()
        if submenu_class:
            submenu_item = None
            if self.submenu_item:
                submenu_item = self.submenu_item
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
