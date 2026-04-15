import django_filters
from django.conf import settings
from django.core.exceptions import FieldError, ValidationError
from django.db.models import Q

from rest_framework.filters import OrderingFilter
from django.db.models.fields import Field
from django.db.models import Model, QuerySet, OrderBy, F, ForeignKey, OneToOneField
from django.db.models.fields import *

from django_toolkit.functions.debug import *
from django_toolkit.functions.base import to_bool, to_number


class FilterSetFactory:
    char_classes = [CharField, TextField, EmailField, SlugField, URLField]
    number_classes = [
        BigAutoField,
        PositiveBigIntegerField,
        BigIntegerField,
        PositiveIntegerField,
        IntegerField,
        DecimalField,
        FloatField,
    ]
    datetime_classes = [DateTimeField, DateField, TimeField]
    bool_classes = [BooleanField]
    #network_classes = [InetAddressField, CidrAddressField]
    foreinkey_classes = [ForeignKey, OneToOneField]

    @staticmethod
    def _lookup_is_valid(queryset: QuerySet, lookup: str, value) -> bool:
        try:
            queryset.filter(**{lookup: value})
            return True
        except (FieldError, ValidationError, TypeError, ValueError):
            return False 

    @staticmethod
    def _get_search_param() -> str:
        rest_framework_settings = getattr(settings, 'REST_FRAMEWORK', {})
        if isinstance(rest_framework_settings, dict):
            search_param = rest_framework_settings.get('SEARCH_PARAM', 'q')
            if isinstance(search_param, str) and search_param.strip():
                return search_param.strip()
        return 'q'

    def _build_field_search_lookups(self, field: Field, search_query: str) -> list[tuple[str, object]]:
        lookups: list[tuple[str, object]] = []

        if field.__class__ in self.char_classes:
            lookups.append((f"{field.name}__icontains", search_query))
            return lookups

        if field.__class__ in self.number_classes:
            parsed_number = to_number(search_query)
            if parsed_number is not None:
                lookups.append((field.name, parsed_number))
            return lookups

        if field.__class__ in self.datetime_classes:
            lookups.append((field.name, search_query))
            return lookups

        if field.__class__ in self.bool_classes:
            parsed_bool = to_bool(search_query)
            if parsed_bool is not None:
                lookups.append((field.name, parsed_bool))
            return lookups

        if field.__class__ in self.foreinkey_classes:
            parsed_number = to_number(search_query)
            if parsed_number is not None:
                lookups.append((f"{field.name}__id", parsed_number))

            remote_model = field.remote_field.model
            for remote_field in remote_model._meta.fields:
                if remote_field.__class__ in self.char_classes:
                    lookups.append((f"{field.name}__{remote_field.name}__icontains", search_query))
                elif remote_field.__class__ in self.number_classes:
                    if parsed_number is not None:
                        lookups.append((f"{field.name}__{remote_field.name}", parsed_number))

            return lookups

        lookups.append((field.name, search_query))
        return lookups

    def _global_search_filter(self, queryset: QuerySet, model: Model, raw_query: str):
        if raw_query is None:
            return queryset

        search_query = str(raw_query).strip()
        if search_query == "":
            return queryset

        search_filter = Q()
        for field in model._meta.fields:
            for lookup, lookup_value in self._build_field_search_lookups(field, search_query):
                if self._lookup_is_valid(queryset, lookup, lookup_value):
                    search_filter |= Q(**{lookup: lookup_value})

        if not search_filter.children:
            return queryset

        return queryset.filter(search_filter).distinct()

    def filterset_class_factory(
            self,
            model,
            request, 
            additional_filters: dict = {},
            exclude_fields: list = []
        ):
        """
        Generate a filterset class based on the model and it fields.
        additional_filters could contain user defined filters which overwrite a generated filter
        """

        model_name = model._meta.object_name
        meta_attributes = {
            "model": model,
            "fields": []
        }
        
        attributes: dict[str, object] = {
            "id": django_filters.ModelMultipleChoiceFilter(
                field_name='id',
                to_field_name='id',
                queryset=model.objects.for_request(request),
            ),
        }

        search_param = self._get_search_param()

        def filter_global_search(filterset_obj, queryset, name, value):
            return self._global_search_filter(queryset=queryset, model=model, raw_query=value)

        attributes["filter_global_search"] = filter_global_search
        attributes[search_param] = django_filters.CharFilter(
            method='filter_global_search',
            label=search_param,
        )

        for field in model._meta.fields:
            if field.name not in exclude_fields:
                # Standard-Filter (exact)
                attributes[field.name] = django_filters.ModelMultipleChoiceFilter(
                    field_name=field.name,
                    to_field_name=field.name,
                    queryset=model.objects.for_request(request),
                )
                
                # String-Filter
                if field.__class__ in self.char_classes:
                    attributes[f"{field.name}__contains"] = django_filters.CharFilter(      # type: ignore
                        field_name=field.name,
                        lookup_expr='icontains',
                    )
                
                # ForeignKey-Filter
                elif field.__class__ in self.foreinkey_classes:
                    # Try to find one unique field of the remote model.
                    # If unique is based on one field generate the filter.
                    # If unique is based on multiple fields the filter must be set via additional_filters
                    remote_model = field.remote_field.model
                    for remote_model_field in remote_model._meta.get_fields():
                        if hasattr(remote_model_field, "unique"):
                            if remote_model_field.unique == True and remote_model_field.name != "id":
                                attributes[field.name] = django_filters.ModelMultipleChoiceFilter(
                                    field_name=f"{field.name}__{remote_model_field.name}".lower(),
                                    to_field_name=remote_model_field.name,
                                    queryset=remote_model.objects.for_request(request),
                                )
                    # Filter the id field of the remote model
                    attributes[f"{field.name}_id"] = django_filters.ModelMultipleChoiceFilter(
                        field_name=f"{field.name}__id",
                        to_field_name='id',
                        queryset=field.related_model.objects.for_request(request),
                    )

        # Zusätzliche (externe) Filter übernehmen
        attributes.update(additional_filters)
            
        # Meta-Klasse erstellen
        meta_class = type('Meta', (), meta_attributes)
        attributes["Meta"] = meta_class     # type: ignore

        # Den User mit geben
        attributes["user"] = request.user

        name = f"{model_name}FilterSet"
        bases = (django_filters.FilterSet,)

        filterset_class =  type(name, bases, attributes)
                
        return filterset_class



class RelatedOrderingFilter(OrderingFilter):
    """
    Filter, for sorting the result using relations
    E.g.: ?ordering=-db_type__label,node__nodename
    """
    _max_related_depth = 1

    @staticmethod
    def _get_verbose_name(field: Field, non_verbose_name: str) -> str:
        return field.verbose_name if hasattr(field, 'verbose_name') else non_verbose_name.replace('_', ' ')

    def _retrieve_all_related_fields(
            self,
            fields: tuple,
            depth: int = 0
    ) -> list:
        valid_fields = []
        if depth > self._max_related_depth:
            return valid_fields
        for field in fields:
            #if field.related_model and field.related_model != model:
            if field.related_model:
                rel_fields = self._retrieve_all_related_fields(
                    field.related_model._meta.get_fields(),
                    depth + 1
                )
                for rel_field in rel_fields:
                    valid_fields.append((
                        f'{field.name}__{rel_field[0]}',
                        self._get_verbose_name(field, rel_field[1])
                    ))
            else:
                valid_fields.append((
                    field.name,
                    self._get_verbose_name(field, field.name),
                ))
        return valid_fields


    def get_valid_fields(self, queryset: QuerySet, view, context: dict | None = None) -> list:
        valid_fields = getattr(view, 'ordering_fields', self.ordering_fields)
        if valid_fields == '__all_related__':
            valid_fields = [
                *self._retrieve_all_related_fields(queryset.model._meta.get_fields()),  
                *[(key, key.title().split('__')) for key in queryset.query.annotations]
            ]
        else:
            if not context:
                context = {}
            valid_fields = super().get_valid_fields(queryset, view, context)
        return valid_fields
    
    
    def remove_invalid_fields(self, queryset, fields, view, request):
        valid_fields = [item[0] for item in self.get_valid_fields(queryset, view, {'request': request})]
        def term_valid(term):
            if term.startswith("-"):
                term = term[1:]
            return term in valid_fields
        return [term for term in fields if term_valid(term)]

    
    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)
        if ordering:
            new_ordering = []
            for ordered_field in ordering:
                if ordered_field.startswith('-'):
                    field = ordered_field[1:]
                    new_ordering.append(OrderBy(F(field), descending=True, nulls_last=True))
                else:
                    field = ordered_field
                    new_ordering.append(OrderBy(F(field), descending=False, nulls_first=True))
            return queryset.order_by(*new_ordering)
        else:
            return queryset
