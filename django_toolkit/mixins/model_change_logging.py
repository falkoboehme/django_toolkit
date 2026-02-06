from django.db import models
from django.utils.translation import gettext_lazy as _


class DTModelChangeLoggingMixin(models.Model):
    """
    Add fields (created, created_user, last_updated und last_updated_user) to models for change tracking
    """
    created = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Created'),
    )
    created_user = models.EmailField(
        blank=True,
        null=True,
        verbose_name=_('Created by user'),
    )
    last_updated = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Last update'),
    )
    last_updated_user = models.EmailField(
        blank=True,
        null=True,
        verbose_name=_('Last update by user'),
    )

    class Meta:
        abstract = True
