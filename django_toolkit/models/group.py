from django.conf import settings
from django.db import models
from django.contrib.auth.models import  Permission, GroupManager
from django.utils.translation import gettext_lazy as _
from .base_models import DTHistoryChangeLoggingModel, DTModelManager
from ..template_context.card_definition import CardDefinition


class DTGroupManager(DTModelManager, GroupManager):
    pass


class DTGroup(DTHistoryChangeLoggingModel):
    name = models.CharField(
        unique=True,
        max_length=100,
        verbose_name=_('Name'),
        help_text=_('Name of the group'),
    )
    permissions = models.ManyToManyField(
        to=Permission,
        blank=True,
        related_name=getattr(settings, 'DT_GROUP_RELATED_NAME_FOR_PERMISSION', 'dtgroup'),
        verbose_name=_('Permissions'),
        help_text=_('Which permissions do users of this group get?'),
    )
    comment = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Comment'),
        help_text=_('Additional remarks'),
    )

    objects = DTGroupManager()


    class Meta(DTHistoryChangeLoggingModel.Meta):
        abstract = True
        ordering = ['name',]
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")
        base_url = 'group'
        cards = [
            [
                CardDefinition(
                    header=_('Group'),
                    fields=['name', 'permissions']
                ),
            ],
            [
                CardDefinition(
                    header=_('Comments'),
                    fields=['comment']
                ),
                CardDefinition(
                    header=_('Internal'),
                    fields=['created', 'created_user', 'last_updated', 'last_updated_user'],
                    ro_fields=['created', 'created_user', 'last_updated', 'last_updated_user'],
                ),
            ]
        ]


    def __str__(self):
        return self.name