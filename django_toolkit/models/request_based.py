from django.conf import settings
from django.db import models
from typing import cast
from django.utils.module_loading import import_string
from ..functions.logging_handler import log_once_per_request

import logging
log = logging.getLogger("toolkit")

class DTRequestBasedQueryset:
    """
    Central queryset filter dispatcher based on model key `app_model`.
    Define methods like `training_sportmodel(self, queryset, request)`.
    """

    def filter_queryset(self, queryset, request=None) -> models.QuerySet:
        model = queryset.model
        method_name = f"{model._meta.app_label}_{model._meta.model_name}"
        model_filter = getattr(self, method_name, None)

        fallback = settings.DT_USER_BASED_QUERYSET_DEFAULT.lower()
        if fallback in ['all', 'default']:
            _fallback_queryset = queryset
        elif fallback in ['empty', 'none']:
            _fallback_queryset = queryset.none()
        else:
            log.error(f"Invalid fallback setting for user-based queryset: '{fallback}'. Using 'none' as fallback.")
            _fallback_queryset = queryset.none()

        if callable(model_filter):
            try:
                filter_result = cast(models.QuerySet, model_filter(queryset=queryset, request=request))
            except TypeError as exc:
                if "unexpected keyword argument 'request'" not in str(exc):
                    raise
                user = getattr(request, "user", None)
                filter_result = cast(models.QuerySet, model_filter(queryset=queryset, user=user))
            if filter_result is None:
                log_once_per_request(
                    log_func=log.warning,
                    request=request,
                    key=f"returned_none:{method_name}:{queryset.model._meta.label}:{fallback}",
                    message=f"Filter method '{method_name}' returned None for model {queryset.model._meta.label}. Using fallback queryset: {fallback}.",
                )
                filter_result = _fallback_queryset
            return filter_result
        log_once_per_request(
            log_func=log.warning,
            request=request,
            key=f"missing_method:{method_name}:{queryset.model._meta.label}:{fallback}",
            message=f"No filter method '{method_name}' found for model {queryset.model._meta.label}. Using fallback queryset: {fallback}.",
        )
        return _fallback_queryset



class DTModelManager(models.Manager):
    def for_request(self, request):
        queryset = self.get_queryset()
        backend = self._get_request_based_queryset_backend()
        return backend.filter_queryset(queryset=queryset, request=request)
    

    @staticmethod
    def _get_request_based_queryset_backend() -> DTRequestBasedQueryset:
        backend_path = getattr(settings, 'DT_USER_BASED_QUERYSET_CLASS', None)
        if not backend_path:
            return DTRequestBasedQueryset()

        backend_cls = import_string(backend_path)
        return backend_cls()