import json
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.forms import BoundField
from django.db import models
from django.conf import settings
from django.http import HttpRequest
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.utils.translation import gettext_lazy as _
from datetime import datetime, date, time
from ..functions.format import django_format_to_python
from ..functions.models import generate_link_to_obj, get_model_base_url
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
            verbose_name = getattr(self._field, "verbose_name", None)
            if verbose_name is not None:
                verbose_name_str = str(verbose_name)
                if verbose_name_str:
                    return verbose_name_str

            related_model = getattr(self._field, "related_model", None)
            if related_model is not None and hasattr(related_model, "_meta"):
                rel_verbose_name = getattr(related_model._meta, "verbose_name_plural", None)
                if rel_verbose_name:
                    return str(rel_verbose_name)
        if self.field_name:
            field_name = self.field_name.replace("_", " ")
            return field_name if field_name else ""
        return ""
    

    @property
    def is_json_field(self) -> bool:
        """Whether the current row represents a JSON model field."""
        if self._field and isinstance(self._field, models.JSONField):
            return True

        if self.bound_field is not None:
            # Form JSONField (update/create views)
            if self.bound_field.field.__class__.__name__ == "JSONField":
                return True

            # Fallback: resolve model field from form meta
            form_model = getattr(getattr(self.bound_field.form, "_meta", None), "model", None)
            if form_model is not None and self.field_name:
                try:
                    model_field = form_model._meta.get_field(self.field_name)
                    return isinstance(model_field, models.JSONField)
                except Exception:
                    pass

        if self.model_instance is not None and self.field_name:
            try:
                model_field = self.model_instance._meta.get_field(self.field_name)
                return isinstance(model_field, models.JSONField)
            except Exception:
                return False

        return False

    @property
    def value(self) -> any:     # type: ignore
        """Field value"""
        raw_value = None
        user = self.request.user if self.request else None
        
        if self.bound_field:
            raw_value = self.bound_field.value()
        elif self.model_instance and self.field_name:
            raw_value = getattr(self.model_instance, self.field_name, None)

        # Handle URLFields by rendering as clickable links
        if self._field and isinstance(self._field, models.URLField) and raw_value:
            return mark_safe(f'<a href="{raw_value}" target="_blank">{raw_value}</a>')

        # Handle ForeignKey fields by generating links to related objects
        if self._field and isinstance(self._field, models.ForeignKey) and raw_value is not None:
            related_obj = getattr(self.model_instance, self.field_name, None)   # type: ignore
            if related_obj is not None:
                return mark_safe(generate_link_to_obj(related_obj, user))

        # Render JSONField values as pretty-printed JSON.
        # In form context return plain text for textarea; in display context return <pre>.
        if self.is_json_field and raw_value is not None:
            try:
                if isinstance(raw_value, str):
                    parsed_value = json.loads(raw_value)
                else:
                    parsed_value = raw_value
                pretty_json = json.dumps(parsed_value, indent=2, ensure_ascii=False, sort_keys=True)
                if self.bound_field:
                    return pretty_json
                return format_html('<pre class="dt-json-value mb-0">{}</pre>', pretty_json)
            except (TypeError, ValueError, json.JSONDecodeError):
                return raw_value
        
        # Handle ManyToMany fields with explicit through models to generate links to related objects
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

        if widget_name == 'SelectMultiple' and self.admin_many_to_many_enabled:
            return 'select_admin_m2m'

        if widget_name in {'Select', 'SelectMultiple'} and self.select_search_enabled:
            return 'select_search'
        
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
    def many_to_many_widget_mode(self) -> str:
        """Configured rendering mode for many-to-many relation fields."""
        configured_mode = getattr(self, 'many_to_many_widget', None)
        if configured_mode is None:
            configured_mode = getattr(self, 'm2m_widget', None)
        if configured_mode is None:
            configured_mode = getattr(self, 'many_to_many_admin', None)

        if isinstance(configured_mode, bool):
            return 'admin' if configured_mode else ''

        if configured_mode is None:
            return ''

        normalized_mode = str(configured_mode).strip().lower()
        if normalized_mode in {'1', 'true', 'yes'}:
            return 'admin'
        return normalized_mode

    @property
    def admin_many_to_many_enabled(self) -> bool:
        """Whether the row should render a dual-list admin-style many-to-many input."""
        if not self.bound_field or not self.multiple:
            return False

        queryset = getattr(self.bound_field.field, 'queryset', None)
        if queryset is None or getattr(queryset, 'model', None) is None:
            return False

        return self.many_to_many_widget_mode in {
            'admin',
            'admin-like',
            'admin_like',
            'filter_horizontal',
            'dual',
            'dual-list',
            'dual_list',
        }

    @property
    def select_search_limit(self) -> int:
        """Threshold for enabling search on select fields."""
        return self._to_positive_int(getattr(settings, 'DT_FORM_SELECT_SEARCH_LIMIT', 0), 0)

    @property
    def select_option_count(self) -> int:
        """Number of currently rendered options in select_data."""
        return len(self.select_data)

    @property
    def select_search_param(self) -> str:
        """API search parameter name, defaults to 'q'."""
        rest_framework_settings = getattr(settings, 'REST_FRAMEWORK', {})
        if isinstance(rest_framework_settings, dict):
            search_param = rest_framework_settings.get('SEARCH_PARAM', 'q')
            if isinstance(search_param, str) and search_param:
                return search_param
        return 'q'

    @property
    def select_search_url(self) -> str:
        """API list endpoint for selectable related model."""
        if not self.bound_field:
            return ""

        queryset = getattr(self.bound_field.field, 'queryset', None)
        related_model = getattr(queryset, 'model', None)
        if related_model is None:
            return ""

        app_label = related_model._meta.app_label
        base_url = get_model_base_url(related_model)
        try:
            return reverse(f"{app_label}-api:{base_url}-list")
        except NoReverseMatch:
            return ""

    @property
    def select_search_enabled(self) -> bool:
        """Whether select should be rendered with ajax-search support."""
        if not self.bound_field:
            return False

        if self.admin_many_to_many_enabled:
            return False

        search_limit = self.select_search_limit
        if search_limit <= 0:
            return False

        if self.select_option_count < search_limit:
            return False

        return bool(self.select_search_url)

    @property
    def select_search_placeholder(self) -> str:
        """Localized placeholder for select search input."""
        return _("Search %(field)s") % {'field': self.display}
    
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

                        if option_value in (None, ''):
                            continue
                        options[str(option_value)] = option_label
            except (TypeError, AttributeError, ValueError):
                # Fallback if optgroups fails
                pass
        
        # Fallback to choices if optgroups didn't work
        if not options and hasattr(self.bound_field.field, 'choices'):
            for choice_value, choice_label in self.bound_field.field.choices:
                if choice_value in (None, ''):
                    continue
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
    def selected_values_json(self) -> str:
        """Selected values as JSON array for client-side scripts."""
        return json.dumps(sorted(self.selected_values))

    @property
    def render_formular(self) -> bool:
        """Whether to render as form input (True) or display value (False)"""
        return self.bound_field is not None
    

    @property
    def field(self):
        """Access to the BoundField for direct template usage"""
        return self.bound_field