from .base import DTView
from django.utils.translation import gettext_lazy as _


class HomeView(DTView):
    template_name = 'django_toolkit/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_title'] = _('Welcome to Django Toolkit')
        context['content_subtitle'] = _('Use the menu to navigate through your models and data.')
        return context