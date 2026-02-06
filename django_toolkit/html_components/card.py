"""
Bootstrap Card Component
"""
from typing import Optional, List, Dict, Any
from .base import Component
from .field import Field


class Card(Component):
    """Bootstrap card with table of fields"""
    
    template_name = 'django_toolkit/includes/card.html'
    
    def __init__(
        self,
        header: str,
        rows: Optional[List[Field]] = None,
        td_display_class: str = '',
        td_value_class: str = '',
        ajax_js: Optional[str] = None
    ):
        self.header = header
        self.rows = rows or []
        self.td_display_class = td_display_class
        self.td_value_class = td_value_class
        self.ajax_js = ajax_js
    
    def add_field(self, field: Field):
        """Add a field to the card"""
        self.rows.append(field)
        return self
    
    def get_context(self) -> Dict[str, Any]:
        return {
            'card': {
                'header': self.header,
                'rows': [field.get_context()['row'] for field in self.rows],
                'td_display_class': self.td_display_class,
                'td_value_class': self.td_value_class,
                'ajax_js': self.ajax_js,
            }
        }
