from ..functions.files import create_file
from pathlib import Path


class MenuCreator:
    """Handles Menu creation and synchronization"""

    _registry: dict = {}

    project_name: str = ""

    def _get_apps_with_menu_models(self) -> dict:
        apps_with_models = {}
        for app_label, models in self._registry.items():
            model_infos = [
                model_info for model_info in models.values()
                if model_info.get("create_menu_entry", True)
            ]
            if model_infos:
                apps_with_models[app_label] = model_infos
        return apps_with_models


    def _auto_create_menu(self) -> set:
        """Auto-sync menu.py for all registered models. Returns True if file was created/modified."""
        file_path=f"{self.project_name}/menu.py"
        files = set()
        apps_with_models = self._get_apps_with_menu_models()

        model_imports = ""
        for app_label in sorted(apps_with_models.keys()):
            model_imports += f"from {app_label}.models import *\n"

        app_sections = ""
        for app_label in sorted(apps_with_models.keys()):
            app_sections += f"    menu_items.append(MenuEntry(title='{app_label.title()}', is_header=True, view_permission=True))\n"
            for model_info in sorted(apps_with_models[app_label], key=lambda item: item["model_class"].__name__):
                model_class_name = model_info["model_class"].__name__
                app_sections += f"    menu_items.append(MenuEntry(model={model_class_name}, request=request))\n"
            app_sections += "\n"

        content = (
            f"from django_toolkit.template_context.menu_entry import MenuEntry\n"
            f"{model_imports}\n"
            f"\n"
            f"def get_side_menu_items(request):\n"
            f"    menu_items = [\n"
            f"        MenuEntry(title='Home', url=('/'), view_permission=True),\n"
            f"    ]\n"
            f"\n"
            f"{app_sections}"
            f"\n"
            f"    menu_items.append(MenuEntry(title='', is_header=True, view_permission=True))\n"
            f"\n"
            f"    return menu_items\n"
        )

        menu_file = Path(file_path)
        if menu_file.exists() and menu_file.read_text(encoding="utf-8") == content:
            return files

        file = create_file(
            file_path=file_path,
            content=content,
            overwrite=False,
        )
        files.add(file) if file else None

        return files
    