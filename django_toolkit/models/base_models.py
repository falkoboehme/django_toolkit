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

class UserBasedQueryset:
    """
    Central queryset filter dispatcher based on model key `app_model`.
    Define methods like `training_sportmodel(self, queryset, user)`.
    """

    def filter_queryset(self, queryset, user=None) -> models.QuerySet:
        model = queryset.model
        method_name = f"{model._meta.app_label}_{model._meta.model_name}"
        model_filter = getattr(self, method_name, None)

        if callable(model_filter):
            return cast(models.QuerySet, model_filter(queryset=queryset, user=user))

        return self._fallback_queryset(queryset)

    def _fallback_queryset(self, queryset) -> models.QuerySet:
        fallback = str(getattr(settings, 'DT_USER_BASED_QUERYSET_DEFAULT', 'none')).lower()
        if fallback in {'empty', 'none'}:
            log.warning(f"Using fallback queryset for model {queryset.model._meta.label}: none")
            return queryset.none()
        log.warning(f"Using fallback queryset for model {queryset.model._meta.label}: all")
        return queryset


def get_user_based_queryset_backend() -> UserBasedQueryset:
    backend_path = getattr(settings, 'DT_USER_BASED_QUERYSET_CLASS', None)
    if not backend_path:
        return UserBasedQueryset()

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
                            #         Card(
                            #             header=_('User'),
                            #             fields=['email', 'groups']
                            #         ),
                            #         Card(
                            #             header=_('Special Rights'),
                            #             fields=['is_active', 'is_staff', 'user_permissions']
                            #         ),
                            #     ],
                            #     [  # Column 1
                            #         Card(
                            #             header=_('Comments'),
                            #             fields=['comment']
                            #         ),
                            #         Card(
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
    

    def get_absolute_url(self):
        """Return the absolute URL for this model instance"""
        base_url = getattr(self._meta, 'base_url', self._meta.model_name)
        url_name = f'{self._meta.app_label}:{base_url}.detail'
        return reverse(url_name, args=[self.pk])

    
    @classmethod
    def for_user(cls, user):
        """Return queryset filtered for a specific user based on the UserBasedQueryset backend."""
        queryset = cls._default_manager.all()
        backend = get_user_based_queryset_backend()
        return backend.filter_queryset(queryset=queryset, user=user)


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
    class Meta(DTHistoryChangeLoggingModel.Meta, DTBaseModel.Meta):
        abstract = True
        history = True
        read_only = False