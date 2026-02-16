from django.db import models
from django.views.generic import View
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.views.generic.base import TemplateResponseMixin, ContextMixin
from ..mixins.dt_context import DTContextMixin



class DTView(LoginRequiredMixin, TemplateResponseMixin, ContextMixin, DTContextMixin, View):
    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        #context.update(**self.fast_dev_context(self.request))
        return self.render_to_response(context)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(**self.dt_context(self.request))
        return context


class DTViewMixins(PermissionRequiredMixin, LoginRequiredMixin, TemplateResponseMixin, ContextMixin, DTContextMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(**self.dt_context(self.request))
        return context
