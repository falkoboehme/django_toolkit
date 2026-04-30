"""
Card Definition Classes for Django Toolkit
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CardFieldDefinition:
    """Single card field definition with optional rendering details.

    Supported options (stored in ``options`` and forwarded via ``row_kwargs``):

    - ``external`` (bool | str)
      Marks a field as external/read-only integration field.
      Behavior:
      - Detail view: field is rendered as usual.
      - Create/Update views: field is skipped and not added to the form.

    - ``many_to_many_widget`` (str | bool)
      Controls many-to-many widget mode in forms.
      Accepted values include ``admin``, ``admin-like``, ``filter_horizontal``,
      ``dual``, ``dual-list`` (and boolean ``True`` as alias for ``admin``).

    - ``m2m_widget`` (str | bool)
      Alias for ``many_to_many_widget``.

    - ``many_to_many_admin`` (str | bool)
      Legacy alias for ``many_to_many_widget``.

    Notes:
    - ``rows``/``textarea_rows`` and ``many_to_many_rows``/``size`` are normalized
      into dedicated attributes and then exposed as
      ``textarea_rows_override`` / ``select_size_override``.
    - Unknown options are currently passed through to ``CardRow`` unchanged.
    """

    name: str
    textarea_rows: int | None = None
    many_to_many_rows: int | None = None
    options: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Card field name must be a non-empty string")
        self.name = self.name.strip()

        if self.textarea_rows is not None:
            try:
                self.textarea_rows = int(self.textarea_rows)
            except (TypeError, ValueError):
                raise ValueError(f"Card field '{self.name}': textarea_rows must be an integer")
            if self.textarea_rows <= 0:
                raise ValueError(f"Card field '{self.name}': textarea_rows must be greater than 0")

        if self.many_to_many_rows is not None:
            try:
                self.many_to_many_rows = int(self.many_to_many_rows)
            except (TypeError, ValueError):
                raise ValueError(f"Card field '{self.name}': many_to_many_rows must be an integer")
            if self.many_to_many_rows <= 0:
                raise ValueError(f"Card field '{self.name}': many_to_many_rows must be greater than 0")

        if not isinstance(self.options, dict):
            self.options = {}

    @property
    def row_kwargs(self) -> dict[str, Any]:
        """Additional kwargs forwarded to CardRow."""
        kwargs = dict(self.options)
        if self.textarea_rows is not None:
            kwargs["textarea_rows_override"] = self.textarea_rows
        if self.many_to_many_rows is not None:
            kwargs["select_size_override"] = self.many_to_many_rows
        return kwargs


def normalize_card_field(field_entry: Any) -> CardFieldDefinition:
    """Normalize supported field config formats to CardFieldDefinition.

    Supported input formats:
    - str: field name
    - dict: at least ``name`` plus optional keys like
      ``rows``/``textarea_rows``, ``many_to_many_rows``/``size`` and any
      supported ``options`` keys (e.g. ``external``, ``many_to_many_widget``)
    - CardFieldDefinition instance
    - object with ``name`` attribute and optional configuration attributes
    """

    def get_valid_name(raw_name: Any) -> str:
        if not isinstance(raw_name, str) or not raw_name.strip():
            raise ValueError("Card field definitions must include a non-empty string in 'name'.")
        return raw_name.strip()

    if isinstance(field_entry, CardFieldDefinition):
        return field_entry

    if isinstance(field_entry, str):
        return CardFieldDefinition(name=field_entry)

    if isinstance(field_entry, dict):
        name = get_valid_name(field_entry.get("name"))
        textarea_rows = field_entry.get("rows", field_entry.get("textarea_rows"))
        many_to_many_rows = field_entry.get("many_to_many_rows", field_entry.get("size"))
        options = {
            key: value
            for key, value in field_entry.items()
            if key not in {"name", "rows", "textarea_rows", "many_to_many_rows", "size"}
        }
        return CardFieldDefinition(
            name=name,
            textarea_rows=textarea_rows,
            many_to_many_rows=many_to_many_rows,
            options=options,
        )

    if hasattr(field_entry, "name"):
        name = get_valid_name(getattr(field_entry, "name", None))
        textarea_rows = getattr(field_entry, "rows", getattr(field_entry, "textarea_rows", None))
        many_to_many_rows = getattr(
            field_entry,
            "many_to_many_rows",
            getattr(field_entry, "size", None),
        )
        options = getattr(field_entry, "options", {})
        if not isinstance(options, dict):
            options = {}
        return CardFieldDefinition(
            name=name,
            textarea_rows=textarea_rows,
            many_to_many_rows=many_to_many_rows,
            options=options,
        )

    raise ValueError(
        f"Unsupported card field definition '{field_entry}'. Use str, dict with 'name', or CardFieldDefinition."
    )


@dataclass
class CardDefinition:
    """
    Defines a card. Used in Models to specify which fields to show in the detail view and how to group them into cards.

    Attributes:
        header: Card header text
        fields: List of field definitions. Each entry can be:
            - str: model field name
            - dict/object with at least `name` and optional details like `rows`
        ro_fields: List of field names that should be read-only (not editable in forms)

    Example:
        CardDefinition(
            header='Personal Info',
            fields=['first_name', 'last_name', {'name': 'comment', 'rows': 6}],
            ro_fields=['created_at'],
        )
    """
    header: str
    fields: list[str | dict | object]   # str for field name, dict or object for detailed definition
    ro_fields: list[str] = None     # type: ignore
    field_definitions: list[CardFieldDefinition] = field(init=False, repr=False)

    def __post_init__(self):
        """Validate card configuration"""
        if not self.fields:
            raise ValueError(f"Card '{self.header}' must have at least one field")
        if self.ro_fields is None:
            self.ro_fields = []

        self.field_definitions = [normalize_card_field(field_entry) for field_entry in self.fields]
        field_names = [field_definition.name for field_definition in self.field_definitions]

        # Validate read_only fields exist in fields
        for ro_field in self.ro_fields:
            if ro_field not in field_names:
                raise ValueError(f"Read-only field '{ro_field}' not in card fields: {field_names}")
        # Check if the whole card is read only
        self.is_read_only = bool(field_names) and set(field_names) == set(self.ro_fields)

    def to_dict(self) -> dict:
        """Convert to dictionary format for backwards compatibility"""
        fields: list[Any] = []
        for field_definition in self.field_definitions:
            if (
                field_definition.textarea_rows is None
                and field_definition.many_to_many_rows is None
                and not field_definition.options
            ):
                fields.append(field_definition.name)
            else:
                field_data: dict[str, Any] = {"name": field_definition.name}
                if field_definition.textarea_rows is not None:
                    field_data["rows"] = field_definition.textarea_rows
                if field_definition.many_to_many_rows is not None:
                    field_data["many_to_many_rows"] = field_definition.many_to_many_rows
                field_data.update(field_definition.options)
                fields.append(field_data)

        result = {
            'header': self.header,
            'fields': fields,
        }
        if self.ro_fields:
            result['ro_fields'] = self.ro_fields
        return result

    def __repr__(self):
        ro_info = f", ro_fields={self.ro_fields}" if self.ro_fields else ""
        return f"CardDefinition(header='{self.header}', fields={self.fields}{ro_info})"
