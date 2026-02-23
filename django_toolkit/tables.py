import django_tables2 as tables
from django.utils.safestring import mark_safe
from django.conf import settings
from django.db import models
from datetime import datetime, date, time
from .mixins.table_pagination import EnhancedPaginator, get_paginate_count
from .template_context.icon import icon_false, icon_true
from .functions.format import django_format_to_python


class DTFormattedColumn(tables.Column):
    """Generic column for formatting date/time values using Django settings"""
    field_type = None  # Must be overridden in subclass
    settings_key = None  # Must be overridden in subclass
    default_format = 'Y-m-d H:i:s'  # Default fallback format
    
    def render(self, value):
        if self.field_type and isinstance(value, self.field_type):
            django_format = getattr(settings, self.settings_key, self.default_format)   # type: ignore
            python_format = django_format_to_python(django_format)
            return value.strftime(python_format)
        return value if value else ''


class DTDateTimeColumn(DTFormattedColumn):
    field_type = datetime
    settings_key = 'DATETIME_FORMAT'
    default_format = 'Y-m-d H:i:s'


class DTDateColumn(DTFormattedColumn):
    field_type = date
    settings_key = 'DATE_FORMAT'
    default_format = 'Y-m-d'


class DTTimeColumn(DTFormattedColumn):
    field_type = time
    settings_key = 'TIME_FORMAT'
    default_format = 'H:i:s'


class DTBaseTable(tables.Table):
    """
    Base table class
    """
    class Meta:
        attrs = {
            'class': 'table table-hover object-list',
        }
    
    def configure(self, request):
        """
        Configure the table for a specific request context. This performs pagination and records
        the user's preferred ordering logic.
        """
        paginate = {
            'paginator_class': EnhancedPaginator,
            'per_page': get_paginate_count(request)
        }
        tables.RequestConfig(request, paginate).configure(self)
    
    def _render_colorfield(self, value):
        return mark_safe(f'<span class="color-label" style="background-color:{value}">&nbsp;</span>')


class DTModelTable(DTBaseTable):
    
    def __init_subclass__(cls, **kwargs):
        """Auto-replace DateTime columns with custom ones"""
        super().__init_subclass__(**kwargs)
        
        if not (hasattr(cls, '_meta') and hasattr(cls._meta, 'model')):
            return
        
        # Mapping from Django field types to custom column classes
        field_type_mapping = {
            models.DateTimeField: DTDateTimeColumn,
            models.DateField: DTDateColumn,
            models.TimeField: DTTimeColumn,
        }
        
        # Check all model fields and set corresponding columns
        for field in cls._meta.model._meta.get_fields():
            field_name = field.name
            for field_type, column_class in field_type_mapping.items():
                if isinstance(field, field_type):
                    if field_name in cls.base_columns:
                        # Replace column of this field with the correct custom column
                        cls.base_columns[field_name] = column_class(accessor=field_name)
                    break
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ID (PK) column should always come first
        if 'id' in self.sequence:
            self.sequence.remove('id')
            self.sequence.insert(0, 'id')

        # Actions column should always come last
        if 'actions' in self.sequence:
            self.sequence.remove('actions')
            self.sequence.append('actions')

    def before_render(self, request):
        """
        Hook to manipulate the table
        """
        return None

    def render_boolean_nice(self, value):
        return icon_true() if value else icon_false()