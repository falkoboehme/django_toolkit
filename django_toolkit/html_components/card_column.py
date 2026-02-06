"""
Bootstrap Card Column Component
"""
from typing import Optional, List, Dict, Any
from .base import Component
from .card import Card


class CardColumn(Component):
    """Column containing multiple cards"""
    
    template_name = 'django_toolkit/includes/card_column.html'
    
    def __init__(self, cards: Optional[List[Card]] = None, width: Optional[int] = None):
        self.cards = cards or []
        self.width = width
    
    def add_card(self, card: Card):
        """Add a card to the column"""
        self.cards.append(card)
        return self
    
    def get_context(self) -> Dict[str, Any]:
        return {
            'card_col': [card.get_context()['card'] for card in self.cards],
            'width': self.width,
        }
