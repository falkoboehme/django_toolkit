import django_tables2 as tables
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.conf import settings
from django.urls import reverse, NoReverseMatch
from django.db import models
from datetime import datetime, date, time
from .mixins.table_pagination import EnhancedPaginator, get_paginate_count
from .template_context.icon import icon_false, icon_true
from .template_context.button import table_actions_button
from .functions.format import django_format_to_python
from .functions.models import get_model_base_url
from .functions.permissions import user_has_model_perms


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
            'class': 'table table-hover dt-table',
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
        self.request = request
        tables.RequestConfig(request, paginate).configure(self)
    
    def _render_colorfield(self, value):
        return mark_safe(f'<span class="color-label" style="background-color:{value}">&nbsp;</span>')


class DTModelTable(DTBaseTable):
    actions = tables.Column(verbose_name='', orderable=False, empty_values=())
    # Per-table toggles:
    # - Set to False to disable the actions column entirely.
    # - Restrict to a subset, e.g. ('history', 'update').
    row_actions_enabled = True
    row_actions = ('history', 'update', 'delete')
    
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
        if not self.row_actions_enabled:
            self.columns.hide('actions')
            return None

        has_any_actions = False
        for row in self.rows:
            if self._build_row_actions(row.record):
                has_any_actions = True
                break

        if has_any_actions:
            self.columns.show('actions')
        else:
            self.columns.hide('actions')

        return None

    def render_boolean_nice(self, value):
        return icon_true() if value else icon_false()

    def _get_enabled_row_actions(self):
        configured = getattr(self, 'row_actions', ())
        if not configured:
            return set()
        enabled_actions = {str(action).strip().lower() for action in configured}
        if 'edit' in enabled_actions:
            enabled_actions.remove('edit')
            enabled_actions.add('update')
        return enabled_actions

    def _build_row_actions(self, record):
        if not self.row_actions_enabled:
            return []

        enabled_actions = self._get_enabled_row_actions()
        if not enabled_actions:
            return []

        actions = []
        model = record._meta.model
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        base_url = get_model_base_url(model)

        # View history
        if 'history' in enabled_actions:
            try:
                history_url = reverse('history:history.object.timeline', args=[app_label, model_name, record.pk])
                actions.append(('View history', history_url, 'bi-clock-history'))
            except NoReverseMatch:
                pass

        request = getattr(self, 'request', None)
        user = getattr(request, 'user', None)
        can_change = bool(user and user_has_model_perms(user, model, 'change'))
        can_delete = bool(user and user_has_model_perms(user, model, 'delete'))
        is_read_only = bool(getattr(model._meta, 'read_only', False))

        # Update
        if 'update' in enabled_actions and can_change and not is_read_only:
            try:
                update_url = reverse(f'{app_label}:{base_url}.update', args=[record.pk])
            except NoReverseMatch:
                update_url = f'/{app_label}/{base_url}/{record.pk}/update/'
            actions.append(('Update', update_url, 'bi-pencil'))

        # Delete
        if 'delete' in enabled_actions and can_delete and not is_read_only:
            try:
                delete_url = reverse(f'{app_label}:{base_url}.delete', args=[record.pk])
            except NoReverseMatch:
                delete_url = f'/{app_label}/{base_url}/{record.pk}/delete/'
            actions.append(('Delete', delete_url, 'bi-trash'))

        return actions

    
    def render_actions(self, record):
        actions = self._build_row_actions(record)
        if not actions:
            return ''

        button_html = table_actions_button(record).render()

        items = []
        for label, href, icon in actions:
            if label == 'Delete':
                object_label = escape(str(record))
                model_verbose = record._meta.model._meta.verbose_name if hasattr(record, '_meta') else 'object'
                items.append(
                    f'<li><a class="dropdown-item dt-table-delete-action" href="#" '
                    f'data-delete-url="{href}" data-delete-object="{object_label}" data-delete-model="{model_verbose}">'
                    f'<i class="bi {icon} me-2"></i>{label}</a></li>'
                )
            else:
                items.append(
                    f'<li><a class="dropdown-item" href="{href}"><i class="bi {icon} me-2"></i>{label}</a></li>'
                )

        menu_html = f'<ul class="dropdown-menu dropdown-menu-end">{"".join(items)}</ul>'
        return mark_safe(f'<div class="dropdown text-end">{button_html}{menu_html}</div>')