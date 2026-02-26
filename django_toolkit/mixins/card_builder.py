"""
Card Builder Mixin for automatic card generation from Django models
"""
from django.db import models
from django.forms import ModelForm
from ..template_context.card_template import CardTemplate
from ..template_context.card_definition import CardDefinition

from ..functions.debug import *

class CardBuilderMixin:
    """
    Mixin to automatically build cards from Django models Meta information.
    Can be used in DetailView, CreateView, UpdateView.
    """
    
    def get_card_definition(self) -> list[list[CardDefinition]]:
        """
        Get card definition configuration from Model Meta.
        
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
        if not hasattr(self.model._meta, 'cards'):  # type: ignore
            raise ValueError(f"Model {self.model.__name__} must define Meta.cards") # type: ignore
        return self.model._meta.cards   # type: ignore
    

    def get_card_context(self):
        context = {}
        card_definition = self.get_card_definition()
        context['card_column_count'] = len(card_definition)   # Number ob card columns
        context['cards'] = []
        for card_col in card_definition:
            card_col_dict = []
            for card_def in card_col:
                card_template = CardTemplate(
                    card_definition=card_def,
                )



    def build_cards(
        self,
        instance: models.Model | None = None,
        form: ModelForm | None = None
    ):
        """
        Build card structure from nested layout configuration.
        
        Args:
            instance: Model instance for DetailView (read-only)
            form: Form instance for CreateView/UpdateView (editable)
            
        Returns:
            CardColumnTemplate ready for rendering
        """
        #card_columns = CardColumnTemplate()
        card_layout = self.get_card_layout()
        pprint(card_layout)
        for column_index, card_list in enumerate(card_layout):
            print(column_index)
            pprint(card_list)

        
        # Process nested format: each element is a column containing cards
        # for column_index, column_cards in enumerate(card_layout):
        #     for card_config in column_cards:
        #         # Support both Card objects and dicts
        #         if isinstance(card_config, CardDefinition):
        #             header = card_config.header
        #             fields = card_config.fields
        #             read_only = card_config.ro_fields or []
        #         else:
        #             # Dict format (backwards compatible)
        #             header = card_config.get('header', '')
        #             fields = card_config.get('fields', [])
        #             read_only = card_config.get('read_only', [])
        #             one_element_per_line = card_config.get('one_element_per_line', [])
                
        #         card = CardTemplate(
        #             header=header,
        #             form=form,
        #             instance=instance,
        #             request=self.request,   # type: ignore
        #             fields=fields,
        #             read_only=read_only,
        #         )
        #         # card_columns.add_card_to_column(card, column_index)
        
        # return card_columns
    

    def get_context_data(self, **kwargs) -> dict:
        """Add cards to context"""
        context = super().get_context_data(**kwargs)    # type: ignore
        
        # Determine if we have form or instance
        form = context.get('form')
        instance = getattr(self, 'object', None)
        
        # Build and add cards
        cards = self.build_cards(instance=instance, form=form)
        context['cards'] = cards.cards
        context['card_column_count'] = cards.card_column_count
        
        return context
