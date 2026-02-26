from django.db import models
from django.views.generic import DetailView
from .base import DTViewMixins
from ..functions.permissions import get_permission_for_model, get_perm_action_from_operation
from ..template_context.modal import confirm_delete_modal


class DTDetailView(DTViewMixins, DetailView):
    """Base DetailView for auto-registered models"""

    model = models.Model
    operation = "detail"
    template_name = f"django_toolkit/generic/{operation}.html"

    @property
    def perm_action(self):
        return get_perm_action_from_operation(self.operation)

    
    def get_permission_required(self) -> list[str]:
        return [get_permission_for_model(self.model, self.perm_action)]


    def get_context_data(self, **kwargs):
        obj = self.get_object()
        context = super().get_context_data(**kwargs)
        context.update(**self.dt_context(self.request))
        context.update(**self.get_card_context(self.request, instance=obj))
        context.update(**self.get_control_buttons(self.request, instance=obj))
        context['content_title'] = str(obj)
        context['modal'] = confirm_delete_modal(obj)
        return context