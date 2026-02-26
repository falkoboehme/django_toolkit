"""
Card Definition Classes for Django Toolkit
"""
from dataclasses import dataclass


@dataclass
class CardDefinition:
    """
    Defines a card. Used in Models to specify which fields to show in the detail view and how to group them into cards.
    
    Attributes:
        header: Card header text
        fields: List of model field names to display
        ro_fields: List of field names that should be read-only (not editable in forms)
    
    Example:
        CardDefinition(
            header='Personal Info', 
            fields=['first_name', 'last_name', 'email', 'created_at', 'groups'],
            ro_fields=['created_at'],
        )
    """
    header: str
    fields: list[str]
    ro_fields: list[str] = None     # type: ignore

    
    def __post_init__(self):
        """Validate card configuration"""
        if not self.fields:
            raise ValueError(f"Card '{self.header}' must have at least one field")
        if self.ro_fields is None:
            self.ro_fields = []
        # Validate read_only fields exist in fields
        for ro_field in self.ro_fields:
            if ro_field not in self.fields:
                raise ValueError(f"Read-only field '{ro_field}' not in card fields: {self.fields}")
        # Check if the whole card is read only
        self.is_read_only = self.fields == self.ro_fields
    

    def to_dict(self) -> dict:
        """Convert to dictionary format for backwards compatibility"""
        result = {
            'header': self.header,
            'fields': self.fields,
        }
        if self.ro_fields:
            result['ro_fields'] = self.ro_fields
        return result
    
    
    def __repr__(self):
        ro_info = f", ro_fields={self.ro_fields}" if self.ro_fields else ""
        return f"CardDefinition(header='{self.header}', fields={self.fields}{ro_info})"
