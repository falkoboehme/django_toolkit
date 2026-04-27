from django.db import models
from django.views.generic import DetailView
from .base import DTViewMixins
from ..functions.permissions import get_permission_for_model_action, get_perm_action_from_operation, user_has_model_perms
from ..template_context.modal import confirm_delete_modal
from ..template_context.button import control_button_update, control_button_delete


class DTDetailView(DTViewMixins, DetailView):
    """Base DetailView for auto-registered models"""

    model = models.Model
    operation = "detail"
    template_name = f"django_toolkit/generic/{operation}.html"

    @property
    def perm_action(self):
        return get_perm_action_from_operation(self.operation)

    
    def get_permission_required(self) -> list[str]:
        return [get_permission_for_model_action(self.model, self.perm_action)]


    def get_context_data(self, **kwargs):
        obj = self.get_object()
        context = super().get_context_data(**kwargs)
        context.update(**self.dt_context(self.request, instance=obj))
        context.update(**self.get_card_context(self.request, instance=obj))
        context.update(**self.get_control_buttons(self.request, instance=obj))
        context['content_title'] = f"{obj._meta.verbose_name}: {obj}"
        context['modal'] = confirm_delete_modal(obj)
        return context