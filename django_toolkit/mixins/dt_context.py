import importlib
from django.conf import settings
from django.utils.safestring import mark_safe
from ..template_context.menu_entry import MenuEntry
from ..template_context.icon import icon_rest_api, icon_swagger_v2, icon_swagger_v3
from ..functions.request import get_app_model_from_request
from ..functions.models import get_app_modelname_id
from ..functions.base import get_project_module_name

import logging
log = logging.getLogger("toolkit")


class DTContextMixin:
    """
    Class to add generic context for each view. For example a dynamic menu.
    """

    def dt_context(self, request, instance=None):
        self._context = super().get_context_data() if hasattr(super(), 'get_context_data') else {}  # type: ignore
        self._add_context(self.global_context, request, instance)
        self._add_context(self.default_context, request, instance)
        self._add_context(self.menu_context, request, instance)
        self._add_context(self.footer_context, request, instance)
        return self._context
    

    def global_context(self, request, instance):
        return {
            'global_project_version': settings.DT_PROJECT_VERSION,
            'global_none': mark_safe(str(getattr(settings, 'DT_DISPLAY_NONE', '---'))),
        }


    def default_context(self, request, instance=None):
        return {
            'page_title': settings.DT_PROJECT_NAME,
            # 'breadcrumbs': ' > '.join(filter(None, [
            #     settings.DT_PROJECT_NAME,
            # ])),
            'breadcrumbs': '',
            'object_identifier': self._get_object_identifier(instance=instance, request=request),
            'content_title': 'content_title',
            'content_subtitle': mark_safe("&nbsp;"),
        }
    

    def menu_context(self, request, instance=None):
        project_name = get_project_module_name()
        menu_file = "menu"
        # log.debug(f"Trying to import {project_name}.{menu_file}")
        try:
            module = importlib.import_module(f"{project_name}.{menu_file}")
            get_side_menu_items = getattr(module, "get_side_menu_items")

            context = {'menu_items': []}
            for menu_entry in get_side_menu_items(request=request):
                if menu_entry.view_permission:
                    context['menu_items'].append(menu_entry)
            return context
        except ModuleNotFoundError as error:
            log.error(f"No menu.py in project folder ({project_name}) found")
        except AttributeError as error:
            log.error(f"No function get_side_menu_items in menu.py found in folder {project_name}")
            raise error


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
                                log.warning(
                                    f"Context key '{key}' already exists ({self._context[key]}), "
                                    f"overwriting it with data from {func.__name__} ({new_context[key]})"
                                )       
                    else:
                        log.warning(
                            f"Context key '{key}' already exists ({self._context[key]}), "
                            f"overwriting it with data from {func.__name__} ({new_context[key]})"
                        )                
        self._context.update(new_context)


    def _get_object_identifier(self, instance=None, request=None):
        if instance:
            app_label, model_name, obj_id = get_app_modelname_id(instance)
            return f"{app_label}.{model_name}:{obj_id} ({str(instance)})"
        elif request:
            app_label, model_name = get_app_model_from_request(request)
            if app_label and model_name:
                return f"{app_label}.{model_name}"
        return None