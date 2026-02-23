from django.conf import settings
from django.utils.safestring import mark_safe
from ..template_context.menu_entry import MenuEntry
from ..template_context.icon import icon_rest_api, icon_swagger_v2, icon_swagger_v3
# from ..templatetags.calc import *

import logging
log = logging.getLogger("django_toolkit")

import importlib
from django.conf import settings
app_label = settings.BASE_DIR.name
menu_file = "menu"
try:
    module = importlib.import_module(f"{app_label}.{menu_file}")
    get_side_menu_items = getattr(module, "get_side_menu_items")
except ModuleNotFoundError as error:
    log.error('No menu.py in project folder found')
except AttributeError as error:
    log.error('No function get_side_menu_items in menu.py found')
    raise error


class DTContextMixin:
    """
    Class to add generic context for each view. For example a dynamic menu.
    """
    _context = {}

    def dt_context(self, request, instance=None):
        self._add_context(self.global_context, request, instance)
        # self._add_context(self.default_context, request, instance)
        self._add_context(self.menu_context, request, instance)
        #self._add_context(self.footer_context, request, instance)
        return self._context
    

    def global_context(self, request, instance):
        return {
            'global_project_version': settings.DT_PROJECT_VERSION,
            'global_none': mark_safe(settings.DT_DISPLAY_NONE),
        }


    # def default_context(self, request, instance=None):
    #     return {
    #         'page_title': settings.DJANGO_FAST_DEV_PROJECT_NAME,
    #         'breadcrumbs': None,
    #         'object_identifier': None,
    #         'content_title': None,
    #         'content_subtitle': None,
    #         'control_buttons': None,
    #     }
    

    def menu_context(self, request, instance=None):
        context = {'menu_items': []}
        user_permissions = request.user.get_all_permissions()

        for menu_entry in get_side_menu_items(request=request):
            menu_entry_access = True
            if isinstance(menu_entry, MenuEntry):
                for required_permission in menu_entry.permissions:
                    if required_permission not in user_permissions:
                        menu_entry_access = False
            if menu_entry_access:
                context['menu_items'].append(menu_entry)
        return context
    

    def footer_context(self, request, instance=None):
        footer_context = {}
        if settings.DT_AUTO_CREATE_API:
            footer_context.update({
                'footer_api': icon_rest_api(),
                'footer_swagger_v2': icon_swagger_v2(),
                'footer_swagger_v3': icon_swagger_v3(),
            })
        return footer_context
    

    def _add_context(self, func, request, instance=None):
        new_context = func(request, instance)
        for key in new_context:
            if key in self._context:
                if self._context[key] != new_context[key]:
                    if isinstance(new_context[key], list):
                        # Compare menu_items (list of classes, __eq__ must be implemented in class)
                        for i, val in enumerate(new_context[key]):
                            if 0 <= i < len(self._context[key]) and val != self._context[key][i]:
                                log.warning(f"Context key '{key}' already exists, overwriting it with data from {func.__name__} ({new_context[key]})")
                    else:
                        log.warning(f"Context key '{key}' already exists, overwriting it with data from {func.__name__} ({new_context[key]})")                
        self._context.update(new_context)

