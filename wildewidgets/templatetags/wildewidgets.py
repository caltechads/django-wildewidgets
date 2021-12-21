from django import template

from ..widgets import Widget


register = template.Library()


class WildewidgetsNode(template.Node):

    def __init__(self, widget):
        self.widget = widget

    def render(self, context):
        if self not in context.render_context:
            context.render_context[self] = (
                template.Variable(self.widget)
            )
        widget = context.render_context[self]
        actual_widget = widget.resolve(context)
        node_context = context.__copy__()
        flattened = node_context.flatten()
        content = actual_widget.get_content(**flattened)
        return content


@register.tag(name="wildewidgets")
def do_wildewidget_render(parser, token):
    token = token.split_contents()
    widget = token.pop(1)
    return WildewidgetsNode(widget)


@register.filter
def is_wildewidget(obj):
    return isinstance(obj, Widget)
