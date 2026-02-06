from django.db.models import options
from django.db import models
from django.utils.translation import gettext_lazy as _
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
        'cards',            # Dict of card-rows, which field is located in which form
                            # cards = [
                            #     [
                            #         {
                            #             'header': _('Exercise'),
                            #             'fields': ['sport', 'name', 'tags' ]
                            #         },
                            #         {
                            #             'header': _('Details'),
                            #             'fields': ['players', 'description', 'purpose' ]
                            #         },
                            #     ],
                            #     [
                            #         {
                            #             'header': _('Comments'),
                            #             'fields': ['comment']
                            #         },
                            #         {
                            #             'header': _('Internal'),
                            #             'fields': ['created', 'created_user', 'last_updated', 'last_updated_user'],
                            #             'read_only': True,
                            #         },
                            #     ]
                            # ]
    )
    
    class Meta:
        abstract = True
        history = False
        read_only = False


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


class DTEnumModel(DTBaseModel):
    """
    Enum Model, for ManyToMany Relationship
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Name'),
    )
    
    class Meta(DTBaseModel.Meta):
        abstract = True
        ordering = ['name',]
    
    def __str__(self):
        return self.name


class DTReadOnlyEnumModel(DTEnumModel):
    """
    Enum Model, for ManyToMany Relationship
    """
   
    class Meta(DTEnumModel.Meta):
        abstract = True
        read_only = True
        ordering = ['name',]
