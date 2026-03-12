import importlib
from typing import Any, cast

from django.core.exceptions import FieldError, ImproperlyConfigured
from django.db import models
from django.db.models import Q, QuerySet
from django.utils.translation import gettext_lazy as _

from .base import DTView
from ..auto_creator.functions import get_table_class_name
from ..functions.models import get_app_model_url, get_user_defined_models
from ..functions.permissions import user_has_model_perms


class GlobalSearchView(DTView):
    template_name = 'django_toolkit/generic/global_search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_query = self.request.GET.get('q', '').strip()

        context['content_title'] = _('Global Search')
        context['content_subtitle'] = search_query if search_query else _('Enter a search term')
        context['search_query'] = search_query
        context['search_results_by_model'] = self.search(search_query) if search_query else []
        return context

    def get_searchable_models(self) -> list[type[models.Model]]:
        return sorted(
            get_user_defined_models(),
            key=lambda model: (model._meta.app_label, model._meta.model_name),
        )

    @staticmethod
    def get_model_search_fields(model: type[models.Model]) -> list[str]:
        configured_fields = getattr(model._meta, 'global_search_fields', ())
        if not configured_fields:
            return []

        return [
            field_name
            for field_name in configured_fields
            if isinstance(field_name, str) and field_name
        ]

    def get_model_queryset(self, model: type[models.Model]) -> QuerySet[Any]:
        manager = model._default_manager
        if hasattr(manager, 'for_request'):
            return cast(QuerySet[Any], manager.for_request(self.request))    # type: ignore[attr-defined]
        return cast(QuerySet[Any], manager.all())

    @staticmethod
    def build_search_query(queryset: QuerySet[Any], search_fields: list[str], search_query: str) -> tuple[Q, list[str]]:
        search_filter = Q()
        valid_fields: list[str] = []

        for field_name in search_fields:
            lookup = f'{field_name}__icontains'
            try:
                queryset.filter(**{lookup: search_query})
            except (FieldError, TypeError, ValueError):
                continue

            search_filter |= Q(**{lookup: search_query})
            valid_fields.append(field_name)

        return search_filter, valid_fields

    def search(self, search_query: str) -> list[dict[str, Any]]:
        grouped_results: list[dict[str, Any]] = []

        for model in self.get_searchable_models():
            if not user_has_model_perms(self.request.user, model, 'view'):   # type: ignore[arg-type]
                continue

            search_fields = self.get_model_search_fields(model)
            if not search_fields:
                continue

            queryset = self.get_model_queryset(model)
            search_filter, valid_fields = self.build_search_query(queryset, search_fields, search_query)
            if not valid_fields:
                continue

            result_queryset = queryset.filter(search_filter).distinct()
            total_count = result_queryset.count()
            if total_count == 0:
                continue

            table = self.get_model_table(model, result_queryset)
            grouped_results.append({
                'title': str(model._meta.verbose_name_plural),
                'list_url': get_app_model_url(model),
                'search_fields': valid_fields,
                'total_count': total_count,
                'table': table,
            })

        return grouped_results

    def get_model_table(self, model: type[models.Model], queryset: QuerySet[Any]) -> Any:
        table_class = self.get_model_table_class(model)
        if table_class is None:
            raise ImproperlyConfigured(
                f"Model '{model._meta.app_label}.{model.__name__}' is searchable but has no table class "
                f"'{get_table_class_name(model.__name__)}' in '{model._meta.app_label}.tables'."
            )

        table = table_class(queryset, prefix=f"{model._meta.app_label}_{model._meta.model_name}-")
        if hasattr(table, 'configure'):
            table.configure(self.request)
        return table

    @staticmethod
    def get_model_table_class(model: type[models.Model]) -> type | None:
        table_class_name = get_table_class_name(model.__name__)
        try:
            tables_module = importlib.import_module(f"{model._meta.app_label}.tables")
        except ModuleNotFoundError:
            return None

        table_class = getattr(tables_module, table_class_name, None)
        if table_class is None:
            return None

        return table_class
