from django.db import models
from django.db.models import QuerySet
from django.views.generic import ListView
from typing import Any, cast
from .base import DTViewMixins
from ..functions.permissions import (
    get_permission_for_model_action,
    get_perm_action_from_operation,
)


class DTListView(DTViewMixins, ListView):
    """Base ListView for auto-registered models"""

    model = models.Model
    template_name = "django_toolkit/generic/table.html"
    operation = "list"
    perm_action = get_perm_action_from_operation(operation)
    table_class = None
    filter_param_prefix = "filter__"
    tab_param_name = "tab"

    def get_permission_required(self) -> list[str]:
        return [get_permission_for_model_action(self.model, self.perm_action)]

    def get_table(self):
        if self.table_class is None:
            return None
        return self.table_class(self.get_queryset())

    def get_filter_fields(self) -> list[models.Field]:
        return [
            field for field in self.model._meta.get_fields()    # type: ignore
            if isinstance(field, models.Field)
            and getattr(field, "concrete", False)
            and not getattr(field, "auto_created", False)
            and not getattr(field, "many_to_many", False)
        ]

    def _get_filter_input_type(self, field):
        if isinstance(field, models.BooleanField):
            return "boolean"
        if isinstance(field, (models.DateTimeField,)):
            return "datetime-local"
        if isinstance(field, (models.DateField,)):
            return "date"
        if isinstance(field, (models.TimeField,)):
            return "time"
        if isinstance(field, (models.IntegerField, models.FloatField, models.DecimalField)):
            return "number"
        return "text"

    def _normalize_filter_value(self, field, raw_value):
        if raw_value is None:
            return None

        value = raw_value.strip() if isinstance(raw_value, str) else raw_value
        if value in ["", None]:
            return None

        if isinstance(field, models.BooleanField):
            lowered = str(value).strip().lower()
            mapping = {
                "true": True,
                "1": True,
                "yes": True,
                "ja": True,
                "false": False,
                "0": False,
                "no": False,
                "nein": False,
            }
            return mapping.get(lowered)

        if isinstance(field, models.ForeignKey):
            try:
                return int(value)
            except (TypeError, ValueError):
                return None

        return value

    def _get_filter_lookup(self, field):
        if isinstance(field, (models.CharField, models.TextField, models.EmailField, models.SlugField)):
            return "icontains"
        if isinstance(field, models.ForeignKey):
            return "id"
        return "exact"

    def apply_filters(self, queryset: QuerySet[Any]) -> QuerySet[Any]:
        for field in self.get_filter_fields():
            field_name = field.name
            param_name = f"{self.filter_param_prefix}{field_name}"
            raw_value = self.request.GET.get(param_name)
            value = self._normalize_filter_value(field, raw_value)
            if value is None:
                continue

            lookup = self._get_filter_lookup(field)
            if lookup == "exact":
                queryset = queryset.filter(**{field_name: value})
            elif lookup == "id":
                queryset = queryset.filter(**{f"{field_name}__id": value})
            else:
                queryset = queryset.filter(**{f"{field_name}__{lookup}": value})

        return queryset

    def get_queryset(self) -> QuerySet[Any]:
        queryset = cast(QuerySet[Any], super().get_queryset())
        return self.apply_filters(queryset)

    def _get_filter_fields_context(self):
        fields_context = []
        for field in self.get_filter_fields():
            fields_context.append({
                "name": field.name,
                "label": field.verbose_name,
                "input_type": self._get_filter_input_type(field),
                "is_boolean": isinstance(field, models.BooleanField),
                "current_value": self.request.GET.get(f"{self.filter_param_prefix}{field.name}", ""),
            })
        return fields_context

    def get_active_tab(self) -> str:
        active_tab = self.request.GET.get(self.tab_param_name, "results")
        return active_tab if active_tab in ["results", "filters"] else "results"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(**self.dt_context(self.request))
        context['content_title'] = self.model._meta.verbose_name_plural     # type: ignore
        context['filter_fields'] = self._get_filter_fields_context()
        context['filter_param_prefix'] = self.filter_param_prefix
        context['active_tab'] = self.get_active_tab()
        context['tab_param_name'] = self.tab_param_name
        table = self.get_table()
        if table is not None:
            table.configure(self.request)
            context["table"] = table
        return context
