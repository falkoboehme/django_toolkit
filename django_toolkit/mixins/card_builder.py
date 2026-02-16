"""
Card Builder Mixin for automatic card generation from Django models
"""
from django.db import models
from django.forms import ModelForm
from ..template_context.card_template import CardTemplate, CardColumnTemplate
from ..template_context.card import Card as CardConfig


class CardBuilderMixin:
    """
    Mixin to automatically build cards from Django models Meta information.
    Can be used in DetailView, CreateView, UpdateView.
    """
    
    # Define card layout in your view class
    card_layout: list[list[CardConfig | dict[str, any]]] | None = None
    
    def get_card_layout(self) -> list[list[CardConfig | dict[str, any]]]:
        """
        Get card layout configuration as nested list (columns with cards).
        
        Priority:
        1. View's card_layout attribute
        2. Model's Meta.cards attribute
        3. View's fields attribute (single column, single card)
        4. All editable model fields (single column, single card)
        
        Returns:
            Nested list: list of columns, each containing list of cards
            
        Example:
            class MyModel(models.Model):
                ...
                class Meta:
                    cards = [
                        [  # Column 0
                            Card(header='Basic', fields=['name', 'email']),
                            Card(header='Address', fields=['street', 'city']),
                        ],
                        [  # Column 1
                            Card(header='Other', fields=['comment']),
                        ],
                    ]
        """
        # 1. Check view's card_layout attribute
        if self.card_layout:
            return self.card_layout
        
        # 2. Check model's Meta.cards
        if hasattr(self.model._meta, 'cards'):
            return self.model._meta.cards
        
        # 3. Use view's fields attribute (single column, single card)
        if hasattr(self, 'fields') and self.fields:
            return [[CardConfig(header=self.model._meta.verbose_name, fields=list(self.fields))]]
        
        # 4. Fallback: all editable model fields (single column, single card)
        fields = [f.name for f in self.model._meta.fields if f.editable]
        return [[CardConfig(header=self.model._meta.verbose_name, fields=fields)]]
    
    def build_cards(
        self,
        instance: models.Model | None = None,
        form: ModelForm | None = None
    ) -> CardColumnTemplate:
        """
        Build card structure from nested layout configuration.
        
        Args:
            instance: Model instance for DetailView (read-only)
            form: Form instance for CreateView/UpdateView (editable)
            
        Returns:
            CardColumnTemplate ready for rendering
        """
        card_columns = CardColumnTemplate()
        card_layout = self.get_card_layout()
        
        # Process nested format: each element is a column containing cards
        for column_index, column_cards in enumerate(card_layout):
            for card_config in column_cards:
                # Support both Card objects and dicts
                if isinstance(card_config, CardConfig):
                    header = card_config.header
                    fields = card_config.fields
                    read_only = card_config.read_only or []
                else:
                    # Dict format (backwards compatible)
                    header = card_config.get('header', '')
                    fields = card_config.get('fields', [])
                    read_only = card_config.get('read_only', [])
                
                card = CardTemplate(
                    header=header,
                    form=form,
                    instance=instance,
                    fields=fields,
                    read_only=read_only
                )
                card_columns.add_card_to_column(card, column_index)
        
        return card_columns
    
    def get_context_data(self, **kwargs):
        """Add cards to context"""
        context = super().get_context_data(**kwargs)
        
        # Determine if we have form or instance
        form = context.get('form')
        instance = getattr(self, 'object', None)
        
        # Build and add cards
        cards = self.build_cards(instance=instance, form=form)
        context['cards'] = cards.cards
        context['card_column_count'] = cards.card_column_count
        
        return context
