from django.conf import settings
from django.db.models import options
from django.db import models
from django.conf import settings
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from typing import cast
from ..template_context.card_definition import CardDefinition
from ..mixins.model_change_logging import DTModelChangeLoggingMixin

import logging
log = logging.getLogger("toolkit")

class DTRequestBasedQueryset:
    """
    Central queryset filter dispatcher based on model key `app_model`.
    Define methods like `training_sportmodel(self, queryset, request)`.
    """

    _LOGGED_WARNINGS_ATTR = "_dt_request_based_queryset_logged_warnings"

    @classmethod
    def _warning_once_per_request(cls, request, key: str, message: str):
        if request is None:
            log.warning(message)
            return

        logged_warnings = getattr(request, cls._LOGGED_WARNINGS_ATTR, None)
        if logged_warnings is None:
            logged_warnings = set()
            setattr(request, cls._LOGGED_WARNINGS_ATTR, logged_warnings)

        if key in logged_warnings:
            return

        logged_warnings.add(key)
        log.warning(message)

    
    def filter_queryset(self, queryset, request=None) -> models.QuerySet:
        model = queryset.model
        method_name = f"{model._meta.app_label}_{model._meta.model_name}"
        model_filter = getattr(self, method_name, None)

        fallback = settings.DT_USER_BASED_QUERYSET_DEFAULT.lower()
        if fallback in ['empty', 'none']:
            _fallback_queryset = queryset.none()
        elif fallback in ['all', 'default']:
            _fallback_queryset = queryset
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
                self._warning_once_per_request(
                    request=request,
                    key=f"returned_none:{method_name}:{queryset.model._meta.label}:{fallback}",
                    message=f"Filter method '{method_name}' returned None for model {queryset.model._meta.label}. Using fallback queryset: {fallback}.",
                )
                filter_result = _fallback_queryset
            return filter_result
        self._warning_once_per_request(
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



class DTBaseModel(models.Model):
    """
    Base model for all models
    """
    
    # Extends Meta information of models
    options.DEFAULT_NAMES = options.DEFAULT_NAMES + (
        'history',          # Track changes of the model
        'read_only',        # Allow only read access
        'base_url',         # Base URL for the model (e.g. 'users')
        'cards',            # List of cards to display in detail view (list of columns with list of cards)
                            # cards = [
                            #     [  # Column 0
                            #         CardDefinition(
                            #             header=_('User'),
                            #             fields=['email', 'groups']
                            #         ),
                            #         CardDefinition(
                            #             header=_('Special Rights'),
                            #             fields=['is_active', 'is_staff', 'user_permissions']
                            #         ),
                            #     ],
                            #     [  # Column 1
                            #         CardDefinition(
                            #             header=_('Comments'),
                            #             fields=['comment']
                            #         ),
                            #         CardDefinition(
                            #             header=_('Internal'),
                            #             fields=['last_login', 'created', 'created_user', 'last_updated', 'last_updated_user', 'is_superuser'],
                            #             read_only=['last_login', 'created', 'created_user', 'last_updated', 'last_updated_user', 'is_superuser']
                            #         ),
                            #     ]
                            # ]
    )
    
    class Meta:
        abstract = True
        history = False
        read_only = False

    objects = DTModelManager()
    

    def get_absolute_url(self):
        """Return the absolute URL for this model instance"""
        base_url = getattr(self._meta, 'base_url', self._meta.model_name)
        url_name = f'{self._meta.app_label}:{base_url}.detail'
        return reverse(url_name, args=[self.pk])

    
class DTReadOnlyModel(DTBaseModel):
    """
    Base model for read only models
    """
    class Meta(DTBaseModel.Meta):
        abstract = True
        history = False
        read_only = True


class DTHistoryModel(DTBaseModel):
    """
    Base model with history in database to track changes
    """
    class Meta(DTBaseModel.Meta):
        abstract = True
        history = True
        read_only = False


class DTHistoryChangeLoggingModel(DTModelChangeLoggingMixin, DTBaseModel):
    """
    Base model with change logging and history to track who did a change and when was it made
    """
    class Meta(DTModelChangeLoggingMixin.Meta, DTBaseModel.Meta):
        abstract = True
        history = True
        read_only = False


class DTEnumModel(DTHistoryChangeLoggingModel):
    """
    Enum Model, for ManyToMany Relationship
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Name'),
    )
    
    class Meta(DTHistoryChangeLoggingModel.Meta):
        abstract = True
        ordering = ['name',]
        cards = [
            [
                CardDefinition(
                    header=_('Name'),
                    fields=['name',],
                ),
            ],
            [
                CardDefinition(
                    header=_('Internal'),
                    fields=['created', 'created_user', 'last_updated', 'last_updated_user'],
                    ro_fields=['created', 'created_user', 'last_updated', 'last_updated_user'],
                ),
            ]
        ]
    
    def __str__(self):
        return self.name


class DTReadOnlyEnumModel(DTEnumModel):
    """
    Enum Model, for ManyToMany Relationship, but read only
    """
   
    class Meta(DTEnumModel.Meta):
        abstract = True
        read_only = True
        ordering = ['name',]


class DTModel(DTHistoryChangeLoggingModel):
    """
    Base model for all models with history and change logging
    """
    pass