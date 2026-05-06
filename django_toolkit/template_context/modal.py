"""
Bootstrap Modal Component
"""
from typing import Optional, Dict, Any
from .base_component import BaseComponent
from django.utils.safestring import mark_safe
from ..functions.models import get_app_model_url


def confirm_delete_modal(instance_or_model):
    model_meta = getattr(instance_or_model, '_meta', None)
    object_meta = getattr(getattr(instance_or_model, '_meta', None), 'model', None)

    # Detail view: a concrete instance with primary key available
    if model_meta is not None and hasattr(instance_or_model, 'pk') and getattr(instance_or_model, 'pk', None) is not None:
        model_name = object_meta._meta.model_name if object_meta is not None else model_meta.model_name
        object_label = str(instance_or_model)
        body = mark_safe(
            f'<p>Are you sure you want to <strong class="text-danger">delete</strong> {model_name} '
            f'<strong>{object_label}</strong>?</p>'
        )
        form_url = f"{get_app_model_url(instance_or_model)}{instance_or_model.id}/delete/"
    else:
        # List view: one shared modal, object is injected dynamically on click
        model_name = model_meta.verbose_name if model_meta is not None else 'object'
        body = mark_safe(
            f'<p>Are you sure you want to <strong class="text-danger">delete</strong> {model_name} '
            '<strong id="dt-delete-object-name"></strong>?</p>'
        )
        form_url = '#'

    return Modal(
        title='Confirm Deletion',
        body=body,
        # TODO: Use Buttons
        footer=mark_safe(
                '<button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>' \
                '<button type="submit" class="btn btn-danger">Delete</button>' \
            ),
        form_url=form_url,
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
