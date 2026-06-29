from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django import forms
from django.forms.models import BaseModelForm
from django.conf import settings
from django.views.generic import View
from django.views.generic.base import TemplateResponseMixin, ContextMixin
from ..models.base_models import DTBaseModel
from ..mixins.dt_context import DTContextMixin
from ..template_context.card_definition import CardDefinition
from ..template_context.card_template import CardTemplate
from ..template_context.button import control_button_create, control_button_update, control_button_delete
from ..functions.permissions import user_has_model_perms



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
                    all_fields_are_read_only = card_config.is_read_only
                    # print(f"Processing card: {card_config}, all_fields_are_read_only={all_fields_are_read_only}, include_read_only_cards={include_read_only_cards}")
                    is_placeholder = not include_read_only_cards and all_fields_are_read_only
                    card = CardTemplate(
                        card_definition=card_config,
                        request=request,
                        instance=instance,
                        form=form,
                        is_placeholder=is_placeholder,
                    )
                    card_context = card.context()
                    if (
                        not include_read_only_cards
                        and not card_context.get('is_placeholder')
                        and not card_context.get('rows')
                    ):
                        continue
                    card_col_dict.append(card_context)
                if card_col_dict:
                    context['cards'].append(card_col_dict)
            context['card_column_count'] = len(context['cards'])
        return context
    

    def get_tab_context(self) -> list[dict]:
        tabs = self.get_tabs()
        default_tab = tabs[0]["key"] if tabs else None
        tabs_context = []
        for tab in tabs:
            tab_key = tab["key"]
            tabs_context.append({
                "key": tab_key,
                "label": tab["label"],
                "template": tab.get("template"),
                "is_active": tab_key == default_tab,
            })
        return tabs_context


    def get_tabs(self) -> list[dict]:
        return []


    def get_control_buttons(self, request, instance=None) -> dict:
        control_buttons = []
        if not self.model._meta.read_only:  # type: ignore
            if instance is not None:   
                if user_has_model_perms(self.request.user, self.model, "change"):   # type: ignore
                    control_buttons.append(control_button_update(instance))
                if user_has_model_perms(self.request.user, self.model, "delete"):   # type: ignore
                    control_buttons.append(control_button_delete(instance))
            else:
                if user_has_model_perms(self.request.user, self.model, "add"):   # type: ignore
                    control_buttons.append(control_button_create(self.model))
        
        return {'control_buttons': control_buttons}

    

    def get_queryset(self):
        return self.model._default_manager.for_request(self.request)    # type: ignore


    def apply_request_based_field_querysets(self, form: BaseModelForm) -> BaseModelForm:
        """Restrict FK/M2M form field querysets using request-based managers when available."""
        for form_field in form.fields.values():
            field_queryset = getattr(form_field, 'queryset', None)
            if field_queryset is None:
                continue

            related_model = getattr(field_queryset, 'model', None)
            if related_model is None:
                continue

            manager = getattr(related_model, '_default_manager', None)
            if manager is None:
                continue

            for_request = getattr(manager, 'for_request', None)
            if callable(for_request):
                form_field.queryset = for_request(self.request)

        return form