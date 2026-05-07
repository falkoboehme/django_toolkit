import logging
from collections import OrderedDict
from django.conf import settings
from django.urls.exceptions import NoReverseMatch
from django.core.paginator import Paginator
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.reverse import reverse
from rest_framework import viewsets, pagination
from rest_framework.filters import SearchFilter, OrderingFilter


from .filtersets import RelatedOrderingFilter, FilterSetFactory
from .metadata import Metadata
from ..functions.models import get_user_apps_with_models
from .mixins.check_permission import CheckPermissionMixin
from ..functions.permissions import raise_permission_denied

from ..functions.debug import *


log = logging.getLogger("toolkit")

DT_API_FILTER_BACKENDS = [DjangoFilterBackend, SearchFilter, RelatedOrderingFilter]



class DocsView(APIView):
    permission_classes = [IsAuthenticated]

    def get_view_name(self):
        return "API Docs"
    
    def get(self, request, format=None):
        return Response(
            OrderedDict(
                (
                    ('swagger-v2', reverse('api-swagger-v2', request=request, format=format)),
                    ('swagger-v3', reverse('api-swagger-v3', request=request, format=format)),
                    ('swagger-v3/download', reverse('api-swagger-v3-download', request=request, format=format)),
                    ('swagger-v3/redoc', reverse('api-swagger-v3-redoc', request=request, format=format)),
                )
            )
        )


class APIRootView(APIView):
    """
    This is the central entrypoint for the API
    """
    exclude_from_schema = True
    swagger_schema = None

    permission_classes = [IsAuthenticated]

    def get_view_name(self):
        return "API Root"

    def get(self, request, format=None):
        url_dict = {}
        user_apps = get_user_apps_with_models()
        user_apps.sort()
        for app_label in user_apps:
            try:
                url_dict[app_label] = reverse(f'{app_label}-api:api-root', request=request, format=format)
            except NoReverseMatch as error:
                log.error(error)
        # Add docs
        url_dict['docs'] = reverse('api-docs', request=request, format=format)
        return Response(OrderedDict(sorted(url_dict.items(), key=lambda item: item[0])))



class APIPagination(pagination.PageNumberPagination):
    """
    Pagination Class für API
    Default-PageSize is set in settings.py
    """
    max_page_size = settings.DT_ITEMS_PER_PAGE_MAX
    page_size_query_param = 'page_size'
    page_query_param = 'page'


class APIListPaginatior(Paginator):
    def page(self, number):
        """Return a Page object for the given 1-based page number."""
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        if top + self.orphans >= self.count:
            top = self.count
        object_dict = {k: self.object_list[k] for k in sorted(self.object_list.keys())[bottom:top]}     # type: ignore
        object_list = [object_dict]
        return self._get_page(object_list, number, self)    # type: ignore


class APIListPagination(APIPagination):
    django_paginator_class = APIListPaginatior



class DTAPIViewSet(CheckPermissionMixin, viewsets.ModelViewSet):
    """
    Base Viewset including CheckPermissionMixin to check if the user has the required rights

    filter_backends:
    - DjangoFilterBackend: filter results via API: ?name=AWS
    - SearchFilter: search in predefined fields (search_fields in ViewSet): ?q=AWS
    - RelatedOrderingFilter: sort results, even for foreign-key-relations: ?ordering=-db_type__label,node__nodename

    Replace OrderingFilter by the improved RelatedOrderingFilter for searching for Foreigen-Keys, even over multiple layers (_max_related_depth in RelatedOrderingFilter)
    """
    permission_classes = [IsAuthenticated]
    search_fields = []
    additional_filters = {}
    filter_backends = DT_API_FILTER_BACKENDS
    pagination_class  = APIPagination
    # activates the RelatedOrderingFilter
    ordering_fields = '__all_related__'
    # extended Metadata class
    metadata_class = Metadata

    def get_queryset(self):
        assert hasattr(self, "model"), f"model not defined in {self.__class__}"
        # Set the filterset_class in the function, so we have access to the request (to get the user) 
        self.filterset_class = FilterSetFactory().filterset_class_factory(
            model=self.model,
            request=self.request,
            additional_filters=self.additional_filters,
        )        
        return self.model.objects.for_request(self.request)
        




class DTReadOnlyAPIViewSet(CheckPermissionMixin, viewsets.ReadOnlyModelViewSet):
    """
    Read only Viewset
    """
    permission_classes = [IsAuthenticated]
    search_fields = []
    additional_filters = {}
    filter_backends = DT_API_FILTER_BACKENDS
    pagination_class = APIPagination
    ordering_fields = '__all_related__'
    metadata_class = Metadata
    http_method_names = ["get", "head", "options"]

    def get_queryset(self):
        assert hasattr(self, "model"), f"model not defined in {self.__class__}"
        self.filterset_class = FilterSetFactory().filterset_class_factory(
            model=self.model,
            request=self.request,
            additional_filters=self.additional_filters,
        )
        return self.model.objects.for_request(self.request)
