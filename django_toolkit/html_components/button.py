"""
Bootstrap Button Component
"""
from typing import Optional, Dict, Any
from .base import Component


class Button(Component):
    """Bootstrap button component"""
    
    template_name = 'django_toolkit/includes/button.html'
    
    def __init__(
        self,
        name: str,
        href: str = '#',
        color: str = 'btn-primary',
        cls: str = 'btn',
        icon: Optional[str] = None,
        attr: Optional[str] = None
    ):
        self.name = name
        self.href = href
        self.color = color
        self.cls = cls
        self.icon = icon
        self.attr = attr
    
    def get_context(self) -> Dict[str, Any]:
        return {
            'button': {
                'name': self.name,
                'href': self.href,
                'color': self.color,
                'cls': self.cls,
                'icon': self.icon,
                'attr': self.attr,
            }
        }
