from django.db import models
from django.views.generic import DetailView
from .base import DTViewMixins
from ..mixins.card_builder import CardBuilderMixin
from ..functions.permissions import (
    get_permission_for_model,
    get_perm_action_from_operation,
)


class DTDetailView(CardBuilderMixin, DTViewMixins, DetailView):
    """Base DetailView for auto-registered models"""

    model = models.Model
    template_name = "django_toolkit/generic/detail.html"
    operation = "detail"
    perm_action = get_perm_action_from_operation(operation)


    def get_permission_required(self) -> list[str]:
        return [get_permission_for_model(self.model, self.perm_action)]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(**self.dt_context(self.request))
        context['content_title'] = str(self.object)     # type: ignore
        return context