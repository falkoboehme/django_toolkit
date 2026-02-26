"""
Bootstrap Modal Component
"""
from typing import Optional, Dict, Any
from .base_component import BaseComponent
from django.utils.safestring import mark_safe
from ..functions.models import get_app_model_url


def confirm_delete_modal(instance):
    model_name = instance._meta.model._meta.model_name
    return Modal(
        title='Confirm Deletion',
        body=mark_safe(f'<p>Are you sure you want to <strong class="text-danger">delete</strong> {model_name} <strong>{str(instance)}</strong>?</p>'),
        # TODO: Use Buttons
        footer=mark_safe(
                '<button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>' \
                '<button type="submit" class="btn btn-danger">Delete</button>' \
            ),
        form_url = f"{get_app_model_url(instance)}{instance.id}/delete/",
        dialog_class='modal-dialog-center',
    )


class Modal(BaseComponent):
    """Bootstrap modal component"""
    
    template_name = 'django_toolkit/includes/modal.html'
    
    def __init__(
        self,
        title: str,
        body: str,
        footer: str = '',
        dialog_class: str = '',
        form_url: Optional[str] = None
    ):
        self.title = title
        self.body = body
        self.footer = footer
        self.dialog_class = dialog_class
        self.form_url = form_url
    
    def get_context(self) -> Dict[str, Any]:
        return {
            'modal': {
                'title': self.title,
                'body': self.body,
                'footer': self.footer,
                'dialog_class': self.dialog_class,
                'form_url': self.form_url,
            }
        }
