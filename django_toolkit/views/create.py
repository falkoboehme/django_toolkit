from django.db import models
from django.views.generic import CreateView
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .base import DTViewMixins
from ..template_context.button import Button, form_button_cancel, form_button_reset, form_button_create
from ..functions.permissions import get_permission_for_model, get_perm_action_from_operation
from ..functions.models import get_app_model_url


class DTCreateView(DTViewMixins, CreateView):
    """Base CreateView for auto-registered models"""

    model = models.Model
    operation = "create"
    template_name = f"django_toolkit/generic/{operation}.html"

    @property
    def perm_action(self):
        return get_perm_action_from_operation(self.operation)


    def get_permission_required(self) -> list[str]:
        return [get_permission_for_model(self.model, self.perm_action)]


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get('form')
        instance = getattr(form, 'instance', None)
        context.update(**self.dt_context(self.request))
        context.update(**self.get_card_context(
            self.request,
            instance=instance,
            form=form,
            include_read_only_cards=False,
        ))
        context['content_title'] = f"{_('Create a new')} {self.model._meta.verbose_name}"
        context['form_buttons'] = self.get_form_buttons()
        return context


    def get_form_buttons(self) -> list[Button]:
        return [
            form_button_cancel(get_app_model_url(self.model)),
            form_button_reset(),
            form_button_create()
        ]
    

    def form_valid(self, form):
        # Add created information to the object
        form.instance.created = timezone.localtime(timezone.now())
        if hasattr(self.request.user, 'email'):
            form.instance.created_user = self.request.user.email    # type: ignore
        return super().form_valid(form)