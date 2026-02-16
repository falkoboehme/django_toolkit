from django.db import models
from django.views.generic import DeleteView
from .base import DTViewMixins
from ..functions.permissions import (
    get_permission_for_model,
    get_perm_action_from_operation,
)


class DTDeleteView(DTViewMixins, DeleteView):
    """Base DeleteView for auto-registered models"""

    model = models.Model
    template_name = "django_toolkit/generic/delete.html"
    operation = "delete"
    perm_action = get_perm_action_from_operation(operation)

    def get_permission_required(self) -> list[str]:
        return [get_permission_for_model(self.model, self.perm_action)]
