"""
Card Definition Classes for Django Toolkit
"""
from dataclasses import dataclass


@dataclass
class Card:
    """
    Defines a card layout for detail/edit views.
    
    Attributes:
        header: Card header text
        fields: List of model field names to display
        read_only: List of field names that should be read-only (not editable in forms)
        column: Optional explicit column index (auto-distributed if None)
    
    Example:
        Card(
            header='Personal Info', 
            fields=['first_name', 'last_name', 'email', 'created_at'],
            read_only=['created_at']  # created_at wird angezeigt, aber nicht editierbar
        )
    """
    header: str
    fields: list[str]
    read_only: list[str] = None     # type: ignore
    column: int | None = None
    
    def __post_init__(self):
        """Validate card configuration"""
        if not self.fields:
            raise ValueError(f"Card '{self.header}' must have at least one field")
        if self.column is not None and self.column < 0:
            raise ValueError(f"Card column must be >= 0, got {self.column}")
        if self.read_only is None:
            self.read_only = []
        # Validate read_only fields exist in fields
        for ro_field in self.read_only:
            if ro_field not in self.fields:
                raise ValueError(f"Read-only field '{ro_field}' not in card fields: {self.fields}")
    
    def to_dict(self) -> dict:
        """Convert to dictionary format for backwards compatibility"""
        result = {
            'header': self.header,
            'fields': self.fields,
        }
        if self.read_only:
            result['read_only'] = self.read_only
        if self.column is not None:
            result['column'] = self.column
        return result
    
    def __repr__(self):
        ro_info = f", read_only={self.read_only}" if self.read_only else ""
        return f"Card(header='{self.header}', fields={self.fields}{ro_info})"
