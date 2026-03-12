from django.utils.safestring import mark_safe
from django.forms import BoundField
from django.db import models
from django.conf import settings
from django.http import HttpRequest
from datetime import datetime, date, time
from ..functions.format import django_format_to_python
from ..functions.models import generate_link_to_obj
from ..template_context.icon import icon_false, icon_true



class CardRow:
    """Wrapper around Django BoundField or model field for consistent interface"""
    
    def __init__(
        self,
        field: models.Field | None = None,
        bound_field: BoundField | None = None,
        model_instance: models.Model | None = None,
        request: HttpRequest | None = None,
        field_name: str | None = None,
        **kwargs
    ):
        """
        Initialize a card row from Django BoundField or Model field.
        
        Args:
            field: Django Field object (for detail views, required when using model_instance)
            bound_field: Django BoundField from a form (for edit views)
            model_instance: Model instance (for detail views)
            request: Django request object (for permission checks and user context)
            field_name: Field/attribute name for virtual fields or properties
            **kwargs: Additional attributes
        """
        self.bound_field = bound_field
        self.model_instance = model_instance
        self._field = field
        self.request = request
        self.field_name = field_name or (bound_field.name if bound_field else (field.name if field else None))
        self.__dict__.update(kwargs)
        # print(f"Initialized CardRow: field_name={self.field_name}, bound_field={self.bound_field}, model_instance={self.model_instance}")

    
    @property
    def id(self) -> str:
        """Field ID for HTML"""
        if self.bound_field:
            return self.bound_field.id_for_label
        field_name = self.field_name or "unknown"
        return f"id_{field_name}"
    
    @property
    def name(self) -> str:
        """Field name for HTML form"""
        if self.bound_field:
            return self.bound_field.html_name
        return self.field_name or ""

    @property
    def display(self) -> str:
        """Field label"""
        if self.bound_field:
            return self.bound_field.label
        if self._field:
            return self._field.verbose_name.capitalize()
        if self.field_name:
            return self.field_name.replace("_", " ").capitalize()
        return ""
    

    @property
    def value(self) -> any:     # type: ignore
        """Field value"""
        raw_value = None
        user = self.request.user if self.request else None
        
        if self.bound_field:
            raw_value = self.bound_field.value()
        elif self.model_instance and self.field_name:
            raw_value = getattr(self.model_instance, self.field_name, None)
        
        # Handle ManyToMany and related fields with links
        if raw_value is not None and hasattr(raw_value, 'all'):
            through_model = getattr(raw_value, 'through', None)
            is_explicit_through = bool(
                through_model is not None
                and hasattr(through_model, '_meta')
                and not getattr(through_model._meta, 'auto_created', True)
            )

            if is_explicit_through and through_model is not None and self.model_instance is not None:
                source_field_name = getattr(raw_value, 'source_field_name', None)
                if isinstance(source_field_name, str) and source_field_name:
                    through_items = through_model.objects.filter(**{source_field_name: self.model_instance})    # type: ignore
                    return mark_safe("<br>".join([generate_link_to_obj(item, user) for item in through_items]))

            return mark_safe("<br>".join([generate_link_to_obj(item, user) for item in raw_value.all()])) 

        if callable(raw_value):
            raw_value = raw_value()

        # Handle iterable values (list/tuple/set) for virtual fields
        if raw_value is not None and isinstance(raw_value, (list, tuple, set)):
            items = []
            for item in raw_value:
                if user and hasattr(item, "pk"):
                    items.append(generate_link_to_obj(item, user))
                else:
                    items.append(str(item))
            return mark_safe(", ".join(items))

        # Format DateTime/Date/Time fields using settings
        if raw_value is not None:
            if isinstance(raw_value, datetime):
                django_datetime_format = getattr(settings, 'DATETIME_FORMAT', 'Y-m-d H:i:s')
                python_format = django_format_to_python(django_datetime_format)
                return raw_value.strftime(python_format)
            elif isinstance(raw_value, date):
                django_date_format = getattr(settings, 'DATE_FORMAT', 'Y-m-d')
                python_format = django_format_to_python(django_date_format)
                return raw_value.strftime(python_format)
            elif isinstance(raw_value, time):
                django_time_format = getattr(settings, 'TIME_FORMAT', 'H:i:s')
                python_format = django_format_to_python(django_time_format)
                return raw_value.strftime(python_format)
        
        # Format Boolean fields as icons (only for display, not in forms)
        if isinstance(raw_value, bool):
            is_display_only = self.request and self.request.method == 'GET' and not self.bound_field
            if is_display_only:
                return icon_true() if raw_value else icon_false()

        return raw_value
    

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
        if self._field:
            return self._field.help_text or ""
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
            'PasswordInput': 'input_password',
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
    def multiple(self) -> bool:
        """Whether field allows multiple selections"""
        if self.bound_field:
            widget = self.bound_field.field.widget
            return bool(getattr(widget, 'allow_multiple_selected', False))
        return False
    
    @property
    def size(self) -> int | str:
        """Size attribute for multiple select fields (e.g. ManyToMany)."""
        if not self.bound_field or not self.multiple:
            return ""

        configured_size = getattr(self, 'select_size_override', None)
        if configured_size is not None:
            size = self._to_positive_int(configured_size, 0)
            return size if size > 0 else ""

        widget_size = getattr(self.bound_field.field.widget, 'attrs', {}).get('size')
        if widget_size is not None:
            size = self._to_positive_int(widget_size, 0)
            return size if size > 0 else ""

        global_size = self._to_positive_int(
            getattr(settings, 'DT_FORM_SELECT_MULTIPLE_SIZE', 0),
            0,
        )
        return global_size if global_size > 0 else ""

    @staticmethod
    def _to_positive_int(value, fallback: int) -> int:
        try:
            parsed = int(value)
            return parsed if parsed > 0 else fallback
        except (TypeError, ValueError):
            return fallback


    @property
    def textarea_rows(self) -> int:
        """Number of rows for textarea widgets."""
        fallback_rows = 2
        global_rows = self._to_positive_int(
            getattr(settings, 'DT_FORM_TEXTAREA_SIZE', fallback_rows),
            fallback_rows,
        )

        configured_rows = getattr(self, 'textarea_rows_override', None)
        if configured_rows is None:
            return global_rows

        return self._to_positive_int(configured_rows, global_rows)
    
    @property
    def select_data(self) -> dict:
        """Options for select fields"""
        if not self.bound_field:
            return {}
        
        widget = self.bound_field.field.widget
        options = {}
        
        # Get the raw value from the BoundField
        raw_value = self.bound_field.value()
        
        # Handle optgroups
        optgroups_function = getattr(widget, 'optgroups', None)
        if callable(optgroups_function):
            try:
                optgroups = optgroups_function(self.name, raw_value, {})
                if not isinstance(optgroups, (list, tuple)):
                    optgroups = []

                for optgroup_name, optgroup_options, optgroup_index in optgroups:
                    for option in optgroup_options:
                        if isinstance(option, dict):
                            option_value = option.get('value')
                            option_label = option.get('label')
                        elif isinstance(option, (list, tuple)) and len(option) >= 2:
                            option_value, option_label = option[0], option[1]
                        else:
                            continue

                        if option_value is None:
                            continue
                        options[str(option_value)] = option_label
            except (TypeError, AttributeError, ValueError):
                # Fallback if optgroups fails
                pass
        
        # Fallback to choices if optgroups didn't work
        if not options and hasattr(self.bound_field.field, 'choices'):
            for choice_value, choice_label in self.bound_field.field.choices:
                options[str(choice_value)] = choice_label
        
        return options

    @property
    def selected_values(self) -> set[str]:
        """Normalized selected values for select widgets"""
        if not self.bound_field:
            return set()

        raw_value = self.bound_field.value()

        if raw_value is None:
            return set()

        if isinstance(raw_value, (list, tuple, set)):
            return {str(value) for value in raw_value if value is not None}

        return {str(raw_value)}

    @property
    def render_formular(self) -> bool:
        """Whether to render as form input (True) or display value (False)"""
        return self.bound_field is not None
    

    @property
    def field(self):
        """Access to the BoundField for direct template usage"""
        return self.bound_field