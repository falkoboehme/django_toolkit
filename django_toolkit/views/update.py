from django.db import models
from django.views.generic import UpdateView
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .base import DTViewMixins
from ..template_context.button import Button, form_button_cancel, form_button_reset, form_button_update
from ..functions.permissions import get_permission_for_model_action, get_perm_action_from_operation
from ..functions.models import get_app_model_url


class DTUpdateView(DTViewMixins, UpdateView):
    """Base UpdateView for auto-registered models"""

    model = models.Model
    operation = "update"
    template_name = f"django_toolkit/generic/{operation}.html"
    
    @property
    def perm_action(self):
        return get_perm_action_from_operation(self.operation)


    def get_permission_required(self) -> list[str]:
        return [get_permission_for_model_action(self.model, self.perm_action)]


    def get_context_data(self, **kwargs):
        obj = self.get_object()
        context = super().get_context_data(**kwargs)
        context.update(**self.dt_context(self.request))
        context.update(**self.get_card_context(self.request, form=context.get('form')))
        context['content_title'] = f"{_('Update')}: {str(obj)}"
        context['form_buttons'] = self.get_form_buttons()
        return context


    def get_form_buttons(self) -> list[Button]:
        return [
            form_button_cancel(get_app_model_url(self.model)),
            form_button_reset(),
            form_button_update()
        ]
    

    def form_valid(self, form):
        # Update last_change information to the object
        form.instance.last_updated = timezone.localtime(timezone.now())
        if hasattr(self.request.user, 'email'):
            form.instance.last_updated_user = self.request.user.email    # type: ignore
        return super().form_valid(form)