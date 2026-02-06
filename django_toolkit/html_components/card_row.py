"""
Bootstrap Card Row Component
"""
from typing import Optional, List, Dict, Any
from .base import Component
from .card_column import CardColumn


class CardRow(Component):
    """Row containing multiple card columns"""
    
    template_name = 'django_toolkit/includes/cards.html'
    
    def __init__(self, columns: Optional[List[CardColumn]] = None):
        self.columns = columns or []
    
    def add_column(self, column: CardColumn):
        """Add a column to the row"""
        self.columns.append(column)
        return self
    
    def get_context(self) -> Dict[str, Any]:
        card_column_count = len(self.columns) if self.columns else 1
        return {
            'cards': [col.get_context()['card_col'] for col in self.columns],
            'card_column_count': card_column_count,
        }
