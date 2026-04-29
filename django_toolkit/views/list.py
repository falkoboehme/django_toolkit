from django.db import models
from django.db.models import QuerySet
from django.core.exceptions import FieldDoesNotExist
from django.views.generic import ListView
from django.utils.translation import gettext_lazy as _
from typing import Any, cast

from .base import DTViewMixins
from ..functions.permissions import (
    get_permission_for_model_action,
    get_perm_action_from_operation,
)
from ..template_context.card_definition import normalize_card_field


class DTListView(DTViewMixins, ListView):
    """Base ListView for auto-registered models"""

    model = models.Model
    template_name = "django_toolkit/generic/list.html"
    operation = "list"
    perm_action = get_perm_action_from_operation(operation)
    table_class = None
    filter_param_prefix = "filter__"


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(**self.dt_context(self.request))
        filter_fields_context = self._get_filter_fields_context()
        context['content_title'] = self.model._meta.verbose_name_plural     # type: ignore
        context['filter_fields'] = filter_fields_context
        context.update(self._get_filter_cards_context(filter_fields_context))
        context['filter_param_prefix'] = self.filter_param_prefix
        context['tabs'] = self.get_tab_context()
        context.update(**self.get_control_buttons(self.request, instance=None))
        table = self.get_table()
        if table is not None:
            table.configure(self.request)
            context["table"] = table
        return context


    def get_tabs(self) -> list[dict]:
        return [*self.get_base_tabs(), *self.get_extra_tabs()]


    def get_base_tabs(self) -> list[dict[str, Any]]:
        return [
            {
                "key": "results",
                "label": str(_("Results")),
                "template": "django_toolkit/includes/table.html",
            },
            {
                "key": "filters",
                "label": str(_("Filters")),
                "template": "django_toolkit/includes/filters.html",
            },
        ]


    def get_extra_tabs(self) -> list[dict[str, Any]]:
        return []


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
        handled_fields: set[str] = set()

        for field in self.get_filter_fields():
            field_name = field.name
            param_name = f"{self.filter_param_prefix}{field_name}"
            raw_value = self.request.GET.get(param_name)
            value = self._normalize_filter_value(field, raw_value)
            if value is None:
                continue

            handled_fields.add(field_name)

            lookup = self._get_filter_lookup(field)
            if lookup == "exact":
                queryset = queryset.filter(**{field_name: value})
            elif lookup == "id":
                queryset = queryset.filter(**{f"{field_name}__id": value})
            else:
                queryset = queryset.filter(**{f"{field_name}__{lookup}": value})

        # Support relation filters like ?filter__cidrs=1 or ?filter__cloud_areas=2
        # for forward and reverse many-to-many relations without per-view overrides.
        for param_name, raw_value in self.request.GET.items():
            if not param_name.startswith(self.filter_param_prefix):
                continue

            field_name = param_name[len(self.filter_param_prefix):]
            if not field_name or field_name in handled_fields:
                continue

            try:
                field = self.model._meta.get_field(field_name)    # type: ignore[union-attr]
            except FieldDoesNotExist:
                continue

            if not getattr(field, "many_to_many", False):
                continue

            try:
                relation_id = int(raw_value)
            except (TypeError, ValueError):
                continue

            queryset = queryset.filter(**{f"{field_name}__id": relation_id})

        queryset = queryset.distinct()

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


    def _build_filter_cards_from_model_meta(self, fields_by_name: dict[str, dict[str, Any]]) -> tuple[list[list[dict[str, Any]]], set[str]]:
        if self.model is None:
            return [], set()

        model_meta_cards = getattr(self.model._meta, "cards", None)
        if not model_meta_cards:
            return [], set()

        filter_cards = []
        used_field_names: set[str] = set()
        for card_column in model_meta_cards:
            column_cards = []
            for card_config in card_column:
                configured_fields = list(getattr(card_config, "fields", []))
                if not configured_fields:
                    continue

                configured_field_names: list[str] = []
                for configured_field in configured_fields:
                    try:
                        configured_field_names.append(normalize_card_field(configured_field).name)
                    except ValueError:
                        continue

                if not configured_field_names:
                    continue

                card_fields = [
                    fields_by_name[field_name]
                    for field_name in configured_field_names
                    if field_name in fields_by_name
                ]

                for field_name in configured_field_names:
                    if field_name in fields_by_name:
                        used_field_names.add(field_name)

                column_cards.append({
                    "header": str(card_config.header),
                    "fields": card_fields,
                })

            filter_cards.append(column_cards)

        return filter_cards, used_field_names


    def _build_filter_cards_fallback(self, filter_fields_context: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
        if not filter_fields_context:
            return []

        chunk_size = 8
        cards = [
            {
                "header": str(_("Filters")),
                "fields": filter_fields_context[index:index + chunk_size],
            }
            for index in range(0, len(filter_fields_context), chunk_size)
        ]

        column_count = 2 if len(cards) > 1 else 1
        columns = [[] for _ in range(column_count)]
        for index, card in enumerate(cards):
            columns[index % column_count].append(card)

        return [column for column in columns if column]


    def _get_filter_cards_context(self, filter_fields_context: list[dict[str, Any]]) -> dict[str, Any]:
        fields_by_name = {field["name"]: field for field in filter_fields_context}
        filter_cards, used_field_names = self._build_filter_cards_from_model_meta(fields_by_name)

        remaining_fields = [
            field
            for field in filter_fields_context
            if field["name"] not in used_field_names
        ]

        if filter_cards and remaining_fields:
            additional_filters_card = {
                "header": str(_("Additional filters")),
                "fields": remaining_fields,
            }
            filter_cards[0].append(additional_filters_card)

        if not filter_cards:
            filter_cards = self._build_filter_cards_fallback(filter_fields_context)

        return {
            "filter_cards": filter_cards,
            "filter_card_column_count": len(filter_cards),
        }
