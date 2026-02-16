"""
Card Template Classes for rendering detail/edit views with cards
Uses Django's native Form and Model systems
"""
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.forms import BoundField
from django.db import models


class CardRow:
    """Wrapper around Django BoundField or model field for consistent interface"""
    
    def __init__(
        self,
        bound_field: BoundField | None = None,
        model_instance: models.Model | None = None,
        field_name: str | None = None,
        display: str | None = None,
        value: any = None,
        **kwargs
    ):
        """
        Initialize a card row from Django BoundField or Model field.
        
        Args:
            bound_field: Django BoundField from a form (for edit views)
            model_instance: Model instance (for detail views)
            field_name: Field name if using model_instance
            display: Override label (optional)
            value: Override value (optional)
            **kwargs: Additional attributes
        """
        self.bound_field = bound_field
        self.model_instance = model_instance
        self.field_name = field_name
        self._display = display
        self._value = value
        self.__dict__.update(kwargs)
    
    @property
    def id(self) -> str:
        """Field ID for HTML"""
        if self.bound_field:
            return self.bound_field.id_for_label
        return f"id_{self.field_name}"
    
    @property
    def display(self) -> str:
        """Field label"""
        if self._display:
            return self._display
        if self.bound_field:
            return self.bound_field.label
        if self.model_instance and self.field_name:
            field = self.model_instance._meta.get_field(self.field_name)
            return field.verbose_name.capitalize()
        return self.field_name or ""
    
    @property
    def value(self) -> any:
        """Field value"""
        if self._value is not None:
            return self._value
        if self.bound_field:
            return self.bound_field.value()
        if self.model_instance and self.field_name:
            return getattr(self.model_instance, self.field_name)
        return None
    
    @property
    def required(self) -> bool:
        """Whether field is required"""
        if self.bound_field:
            return self.bound_field.field.required
        return False
    
    @property
    def help(self) -> str:
        """Help text"""
        if self.bound_field:
            return self.bound_field.help_text or ""
        if self.model_instance and self.field_name:
            field = self.model_instance._meta.get_field(self.field_name)
            return field.help_text or ""
        return ""
    
    @property
    def form(self) -> str:
        """Widget type for rendering"""
        if not self.bound_field:
            return "display"  # Read-only display
        
        widget = self.bound_field.field.widget
        widget_name = widget.__class__.__name__     # type: ignore
        
        # Map Django widgets to template names
        widget_map = {
            'TextInput': 'input_text',
            'EmailInput': 'input_text',
            'URLInput': 'input_text',
            'NumberInput': 'input_number',
            'Textarea': 'textarea',
            'CheckboxInput': 'input_checkbox',
            'Select': 'select',
            'SelectMultiple': 'select',
            'DateInput': 'input_date',
            'DateTimeInput': 'input_datetime',
            'TimeInput': 'input_time',
        }
        
        return widget_map.get(widget_name, 'input_text')
    
    @property
    def render_formular(self) -> bool:
        """Whether to render as form input (True) or display value (False)"""
        return self.bound_field is not None
    
    @property
    def field(self):
        """Access to the BoundField for direct template usage"""
        return self.bound_field


class CardTemplate:
    """Represents a card with header and fields"""
    
    def __init__(
        self,
        header: str,
        form: any = None,
        instance: models.Model | None = None,
        fields: list[str] | None = None,
        read_only: list[str] | None = None,
        rows: list[CardRow] | None = None,
        td_display_class: str = "",
        td_value_class: str = "",
        ajax_js: str = "",
        template: str = "django_toolkit/includes/card.html",
        **kwargs
    ):
        """
        Initialize a card template.
        
        Args:
            header: Card header text
            form: Django Form instance (for edit views)
            instance: Model instance (for detail views)
            fields: List of field names to include
            read_only: List of field names that should be read-only (not editable in forms)
            rows: Pre-built CardRow objects (optional)
            td_display_class: CSS class for display column
            td_value_class: CSS class for value column
            ajax_js: JavaScript code to inject
            template: Path to the template file
            **kwargs: Additional attributes
        """
        self.header = header
        self._form = form
        self._instance = instance
        self._fields = fields or []
        self._read_only = read_only or []
        self._rows = rows
        self.td_display_class = td_display_class
        self.td_value_class = td_value_class
        self.ajax_js = ajax_js
        self.template = template
        self.__dict__.update(kwargs)
    
    @property
    def rows(self) -> list[CardRow]:
        """Generate rows automatically from form or instance"""
        if self._rows:
            return self._rows
        
        rows = []
        for field_name in self._fields:
            # Check if field should be read-only
            is_read_only = field_name in self._read_only
            
            if self._form and field_name in self._form.fields and not is_read_only:
                # Editable form field
                rows.append(CardRow(bound_field=self._form[field_name]))
            elif self._instance:
                # Read-only display (DetailView or read_only field in form)
                rows.append(CardRow(
                    model_instance=self._instance,
                    field_name=field_name
                ))
        
        return rows
    
    def add_row(self, row: CardRow) -> None:
        """Add a row to the card"""
        if self._rows is None:
            self._rows = []
        self._rows.append(row)
    
    def render(self, context: dict | None = None) -> str:
        """
        Render the card using its template.
        
        Args:
            context: Additional context to pass to the template
            
        Returns:
            Rendered HTML as safe string
        """
        ctx = context or {}
        ctx['card'] = self
        if self._form:
            ctx['form'] = self._form
        return mark_safe(render_to_string(self.template, ctx))
    
    def __str__(self) -> str:
        return self.render()


class CardColumnTemplate:
    """Represents a collection of cards in columns"""
    
    def __init__(
        self,
        cards: list[list[CardTemplate]] | None = None,
        template: str = "django_toolkit/includes/cards.html",
        **kwargs
    ):
        """
        Initialize card columns.
        
        Args:
            cards: List of card columns, where each column is a list of CardTemplate objects
            template: Path to the template file
            **kwargs: Additional attributes
        """
        self.cards = cards or []
        self.template = template
        self.__dict__.update(kwargs)
    
    @property
    def card_column_count(self) -> int:
        """Get the number of card columns"""
        return len(self.cards) if self.cards else 1
    
    def add_column(self, column: list[CardTemplate]) -> None:
        """Add a column of cards"""
        self.cards.append(column)
    
    def add_card_to_column(self, card: CardTemplate, column_index: int = 0) -> None:
        """
        Add a card to a specific column.
        
        Args:
            card: CardTemplate to add
            column_index: Index of the column (creates new columns if needed)
        """
        # Ensure column exists
        while len(self.cards) <= column_index:
            self.cards.append([])
        
        self.cards[column_index].append(card)
    
    def render(self, context: dict | None = None) -> str:
        """
        Render all card columns using the template.
        
        Args:
            context: Additional context to pass to the template
            
        Returns:
            Rendered HTML as safe string
        """
        ctx = context or {}
        ctx['cards'] = self.cards
        ctx['card_column_count'] = self.card_column_count
        return mark_safe(render_to_string(self.template, ctx))
    
    def __str__(self) -> str:
        return self.render()


