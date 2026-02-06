"""
Bootstrap Modal Component
"""
from typing import Optional, Dict, Any
from .base import Component


class Modal(Component):
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
