from django.db import models
from django.utils.translation import gettext_lazy as _
from .cidr.field import CIDRField


class AbstractDTApiToken(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_('Name')
    )
    token_hash = models.CharField(
        max_length=64,
        unique=True,
        verbose_name=_('Token Hash')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    valid_until = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Valid Until')
    )

    class Meta:
        abstract = True

    def __str__(self):
        if hasattr(self, 'user'):
            return f"{self.name} ({self.user})"     # type: ignore
        return self.name


class AbstractDTApiTokenAllowedCIDR(models.Model):
    cidr = CIDRField(
        db_index=True,
        verbose_name=_('CIDR')
    )

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.cidr)