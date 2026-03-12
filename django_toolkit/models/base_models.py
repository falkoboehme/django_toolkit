
from django.db.models import options
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from .request_based import DTModelManager
from ..template_context.card_definition import CardDefinition
from ..mixins.model_change_logging import DTModelChangeLoggingMixin




class DTBaseModel(models.Model):
    """
    Base model for all models
    """
    
    # Extends Meta information of models
    options.DEFAULT_NAMES = options.DEFAULT_NAMES + (
        'history',          # Track changes of the model
        'read_only',        # Allow only read access
        'base_url',         # Base URL for the model (e.g. 'users')
        'global_search_fields',
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
        global_search_fields = ()

    objects = DTModelManager()
    

    def get_absolute_url(self):
        """Return the absolute URL for this model instance"""
        app_label = self._meta.app_label
        base_url = getattr(self._meta, 'base_url', self._meta.model_name)
        return reverse(f'{app_label}:{base_url}.detail', args=[self.pk])

    
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
        global_search_fields = ['name']
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
