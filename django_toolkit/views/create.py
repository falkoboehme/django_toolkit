from django.db import models
from django.views.generic import CreateView
from .base import DTViewMixins
from ..mixins.card_builder import CardBuilderMixin
from ..functions.permissions import (
    get_permission_for_model,
    get_perm_action_from_operation,
)


class DTCreateView(CardBuilderMixin, DTViewMixins, CreateView):
    """Base CreateView for auto-registered models"""

    model = models.Model
    template_name = "django_toolkit/generic/add.html"
    operation = "create"
    perm_action = get_perm_action_from_operation(operation)

    def get_permission_required(self) -> list[str]:
        return [get_permission_for_model(self.model, self.perm_action)]
