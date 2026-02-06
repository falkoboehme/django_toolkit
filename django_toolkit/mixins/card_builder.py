"""
Card Builder Mixin for Django Models
"""
from django.db import models
from typing import List, Optional
from ..html_components import Card, CardColumn, CardRow, Field


class CardBuilderMixin:
    """
    Mixin to add card building capabilities to Django models
    """
    
    @classmethod
    def field(cls, field_name: str, **kwargs) -> Field:
        """
        Create a Field component from a model field name.
        Automatically extracts verbose_name, form type, required, help_text from model field.
        
        Args:
            field_name: Name of the model field
            **kwargs: Override any auto-detected values (display, form, required, help_text, etc.)
        
        Example:
            cls.field('email')  # Uses all defaults from model field
            cls.field('email', form='input_text')  # Override form type
        """
        try:
            model_field = cls._meta.get_field(field_name)   # type: ignore
            return cls._create_field_from_model_field(field_name, model_field, **kwargs)
        except:
            # Fallback for properties or custom fields
            return Field(
                field_id=field_name,
                display=kwargs.get('display', field_name),
                form=kwargs.get('form', 'input_text'),
                **{k: v for k, v in kwargs.items() if k not in ['display', 'form']}
            )
    
    @classmethod
    def fields(cls, *field_names, **kwargs) -> List[Field]:
        """
        Create multiple Field components from model field names.
        
        Args:
            *field_names: Names of the model fields
            **kwargs: Common overrides for all fields
        
        Example:
            cls.fields('email', 'name', 'phone')
        """
        return [cls.field(name, **kwargs) for name in field_names]
    
    @classmethod
    def get_card_layout(cls) -> Optional[CardRow]:
        """
        Override this method to define card layout for the model.
        Uses cls.field() or cls.fields() to automatically create fields from model definition.
        
        Example:
            @classmethod
            def get_card_layout(cls):
                return CardRow([
                    CardColumn([
                        Card('User Data', [
                            cls.field('email'),  # Auto: verbose_name, form type, required
                            cls.field('name')
                        ])
                    ])
                ])
            
            # Or with multiple fields:
            @classmethod
            def get_card_layout(cls):
                return CardRow([
                    CardColumn([
                        Card('User Data', cls.fields('email', 'name', 'phone'))
                    ])
                ])
        """
        # Try to build from Meta.cards if available
        if hasattr(cls._meta, 'cards') and cls._meta.cards: # type: ignore
            return cls._build_cards_from_meta()
        return None
    
    @classmethod
    def _build_cards_from_meta(cls) -> CardRow:
        """
        Build CardRow from Meta.cards definition
        """
        columns = []
        
        for card_col in cls._meta.cards:    # type: ignore
            cards = []
            for card_def in card_col:
                fields = []
                for field_name in card_def.get('fields', []):
                    # Get field from model
                    try:
                        model_field = cls._meta.get_field(field_name)   # type: ignore
                        field = cls._create_field_from_model_field(field_name, model_field)
                        fields.append(field)
                    except:
                        # Field might be a property or custom field
                        pass
                
                card = Card(
                    header=card_def.get('header', ''),
                    rows=fields,
                    td_display_class=card_def.get('td_display_class', ''),
                    td_value_class=card_def.get('td_value_class', ''),
                )
                cards.append(card)
            
            columns.append(CardColumn(cards))
        
        return CardRow(columns)
    
    @classmethod
    def _create_field_from_model_field(cls, field_name: str, model_field, **kwargs) -> Field:
        """
        Create a Field component from a Django model field
        
        Args:
            field_name: Name of the field
            model_field: Django model field instance
            **kwargs: Override any auto-detected values
        """
        
        # Determine form type based on field type
        form_type = 'input_text'  # default
        
        if isinstance(model_field, models.BooleanField):
            form_type = 'input_checkbox'
        elif isinstance(model_field, models.TextField):
            form_type = 'textarea'
        elif isinstance(model_field, models.IntegerField):
            form_type = 'input_number'
        elif isinstance(model_field, models.DateTimeField):
            form_type = 'input_datetime'
        elif isinstance(model_field, models.DateField):
            form_type = 'input_date'
        elif isinstance(model_field, (models.ForeignKey, models.ManyToManyField)):
            form_type = 'select'
        
        # Build field with auto-detected values, allow kwargs to override
        return Field(
            field_id=kwargs.get('field_id', field_name),
            display=kwargs.get('display', model_field.verbose_name or field_name),
            form=kwargs.get('form', form_type),
            required=kwargs.get('required', not model_field.blank and not model_field.null),
            help_text=kwargs.get('help_text', model_field.help_text or ''),
            **{k: v for k, v in kwargs.items() if k not in ['field_id', 'display', 'form', 'required', 'help_text']}
        )
    
    def get_instance_card_layout(self) -> Optional[CardRow]:
        """
        Get card layout for this specific instance (can access instance data)
        """
        return self.__class__.get_card_layout()
