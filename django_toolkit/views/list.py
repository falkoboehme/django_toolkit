from django.db import models
from django.views.generic import ListView
from .base import DTViewMixins
from ..functions.permissions import (
    get_permission_for_model,
    get_perm_action_from_operation,
)


class DTListView(DTViewMixins, ListView):
    """Base ListView for auto-registered models"""

    model = models.Model
    template_name = "django_toolkit/generic/table.html"
    operation = "list"
    perm_action = get_perm_action_from_operation(operation)
    table_class = None

    def get_permission_required(self) -> list[str]:
        return [get_permission_for_model(self.model, self.perm_action)]

    def get_table(self):
        if self.table_class is None:
            return None
        return self.table_class(self.get_queryset())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(**self.dt_context(self.request))
        context['content_title'] = self.model._meta.verbose_name_plural     # type: ignore
        table = self.get_table()
        if table is not None:
            table.configure(self.request)
            context["table"] = table
        return context
