from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from ..functions.models import get_app_model_url
from .icon import SVGIcon
from .base_component import BaseComponent


def menu_button_create(model):
    return Button(
            name='',
            href=f'{get_app_model_url(model)}create/',
            color='green',
            icon=mark_safe(SVGIcon(icon_name="plus-thick", width=12, height=12, fillcolor="currentcolor", viewbox="2 2 20 22").render()),
            cls="btn btn-sm lh-1 dt-menu-create-btn"
        )

def goto_button(url, text, color='blue'):
    return Button(
        name=_(text),
        href=url,
        color=color,
    )

def control_button_create(model):
    return Button(
        name=_("Create"),
        href=f'{get_app_model_url(model)}create/',
        color='green',
        icon=mark_safe(SVGIcon(icon_name="plus-thick", fillcolor="currentcolor", viewbox="2 2 24 24").render()),
    )

def control_button_update(obj):
    return Button(
        name=_("Update"),
        href=f'{get_app_model_url(obj._meta.model)}{obj.id}/update/',
        color='yellow',
        icon=mark_safe(SVGIcon(icon_name="pencil-outline", fillcolor="currentcolor", viewbox="2 2 24 24").render()),
    )

def control_button_delete(obj):
    return Button(
        name=_("Delete"),
        href='#',
        color='red',
        icon=mark_safe(SVGIcon(icon_name="trash-can-outline", fillcolor="currentcolor", viewbox="2 2 24 24").render()),
        attr=mark_safe('data-bs-toggle="modal" data-bs-target="#deleteAskModal"'),
    )

def form_button_cancel(url):
    return Button(
        name=_("Cancel"),
        href=url,
        color='red-outline',
    )

def form_button_reset():
    return Button(
        name=_("Reset"),
        href='#',
        color='blue-outline',
        attr=mark_safe('type="reset"'),
    )

def form_button_create():
    return Button(
        name=_("Create"),
        href='#',
        color='green',
        attr=mark_safe('type="submit"'),
    )


def form_button_update():
    return Button(
        name=_("Update"),
        href='#',
        color='yellow',
        attr=mark_safe('type="submit"'),
    )


def form_button_save():
    return Button(
        name=_("Save"),
        href='#',
        color='blue',
        attr=mark_safe('type="submit"'),
    )


class Button(BaseComponent):
    """
    Class to define a nice a-Tag with the look of a button

    :param name: `str` text shown on the "button"
    :param href: `str` url to use in the link
    :param color: `str` color of the "button"
    :param icon: `str` icon to display inside the "button"
    :param cls: `str` additional classes for the a-Tag
    :param attr: `str` additional attributes inside the a-Tag
    """

    color_class_mapping = {
        'blue': 'btn-primary',
        'grey': 'btn-secondary',
        'green': 'btn-success',
        'red': 'btn-danger',
        'yellow': 'btn-warning',
        'cyan': 'btn-info',
        'light': 'btn-light',
        'dark': 'btn-dark',
        'link': 'btn-link',

        'blue-outline': 'btn-outline-primary',
        'grey-outline': 'btn-outline-secondary',
        'green-outline': 'btn-outline-success',
        'red-outline': 'btn-outline-danger',
        'yellow-outline': 'btn-outline-warning',
        'cyan-outline': 'btn-outline-info',
        'light-outline': 'btn-outline-light',
        'dark-outline': 'btn-outline-dark',
    }

    template_name = 'django_toolkit/includes/button.html'

    def __init__(
            self,
            name,
            href,
            color='blue',
            icon=None,
            cls="btn btn-sm",
            attr=None,
        ):
        self.name = name
        self.href = href
        self.color = self.color_class_mapping[color]
        self.icon = icon
        self.cls = cls
        self.attr = attr

    def get_context(self):
        return {
            'button': self,
        }

    