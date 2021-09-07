from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import View


class TableActionFormView(View):
    http_method_names = ['post']
    url = ''
    
    
    def process_form_action(self, action, items):
        pass
    
    def post(self, request, *args, **kwargs):
        checkboxes = request.POST.getlist('checkbox')
        action = request.POST.get('action')
        self.process_form_action(action, checkboxes)
        return HttpResponseRedirect(self.url)
