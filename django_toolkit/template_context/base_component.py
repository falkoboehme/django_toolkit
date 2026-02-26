"""
Base Component Class for django_toolkit HTMLComponents
"""
from django.template.loader import render_to_string
from typing import Optional, Dict, Any


class BaseComponent:
    """Base class for all components"""
    
    template_name: str | None = None  # Must be set in subclasses
    
    def render(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Render the component to HTML"""
        if not self.template_name:
            raise NotImplementedError("template_name must be defined")
        
        component_context = self.get_context()
        if context:
            component_context.update(context)
        
        return render_to_string(self.template_name, component_context)
    
    def get_context(self) -> Dict[str, Any]:
        """Get the context dictionary for rendering"""
        raise NotImplementedError("get_context must be implemented")
    
    def __str__(self) -> str:
        """Allow string conversion for direct template usage"""
        return self.render()
