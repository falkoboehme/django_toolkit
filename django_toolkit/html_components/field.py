"""
Bootstrap Form Field Component
"""
from typing import Any, Dict
from .base import Component


class Field(Component):
    """Bootstrap form field in card"""
    
    template_name = 'django_toolkit/includes/field.html'
    
    def __init__(
        self,
        field_id: str,
        display: str,
        form: str,
        value: Any = None,
        required: bool = False,
        help_text: str = '',
        render_formular: bool = True,
        **kwargs
    ):
        self.field_id = field_id
        self.display = display
        self.form = form
        self.value = value
        self.required = required
        self.help_text = help_text
        self.render_formular = render_formular
        self.extra = kwargs
    
    def get_context(self) -> Dict[str, Any]:
        return {
            'row': {
                'id': self.field_id,
                'display': self.display,
                'form': self.form,
                'value': self.value,
                'required': self.required,
                'help': self.help_text,
                'render_formular': self.render_formular,
                **self.extra
            }
        }
