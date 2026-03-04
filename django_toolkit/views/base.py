from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.views.generic import View
from django.views.generic.base import TemplateResponseMixin, ContextMixin
from ..models.base_models import DTBaseModel
from ..mixins.dt_context import DTContextMixin
from ..template_context.card_definition import CardDefinition
from ..template_context.card_template import CardTemplate
from ..template_context.button import control_button_create, control_button_update, control_button_delete



class DTView(LoginRequiredMixin, TemplateResponseMixin, ContextMixin, DTContextMixin, View):
    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return self.render_to_response(context)
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(**self.dt_context(self.request))
        return context



class DTViewMixins(PermissionRequiredMixin, LoginRequiredMixin, TemplateResponseMixin, ContextMixin, DTContextMixin):
    model = DTBaseModel    # must be set in each ModelView
    
    def get_card_context(self, request, instance=None, form=None, include_read_only_cards=True) -> dict:
        context = {}
        if hasattr(self.model._meta, "cards"):
            meta_cards = self.model._meta.cards     # type: ignore
            context['cards'] = []
            for card_col in meta_cards:
                card_col_dict = []
                for card_config in card_col:
                    if not isinstance(card_config, CardDefinition):
                        raise TypeError(
                            f"Meta.cards must contain CardDefinition objects, got {type(card_config).__name__}"
                        )
                    all_fields_are_read_only = set(card_config.fields) == set(card_config.ro_fields)
                    is_placeholder = not include_read_only_cards and all_fields_are_read_only
                    card = CardTemplate(
                        card_definition=card_config,
                        request=request,
                        instance=instance,
                        form=form,
                        is_placeholder=is_placeholder,
                    )
                    card_col_dict.append(card.context())
                if card_col_dict:
                    context['cards'].append(card_col_dict)
            context['card_column_count'] = len(context['cards'])
        return context
    

    def get_control_buttons(self, request, instance=None) -> dict:
        control_buttons = []
        if instance is not None:
            control_buttons.append(control_button_update(instance))
            control_buttons.append(control_button_delete(instance))
        
        return {'control_buttons': control_buttons}
    

    def get_queryset(self):
        return self.model._default_manager.for_request(self.request)