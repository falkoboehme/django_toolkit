from ..functions.files import insert_lines_in_file, create_file
from ..template_context.menu_entry import MenuEntry


class MenuCreator:
    """Handles Menu creation and synchronization"""

    _registry: dict = {}

    project_name: str = ""


    def _auto_create_menu(self) -> set:
        """Auto-sync menu.py for all registered models. Returns True if file was created/modified."""
        files = set()
        model_imports = ""
        for app_label, models in self._registry.items():
            model_imports += f"from {app_label}.models import *\n"
        file = create_file(
            file_path=f"{self.project_name}/menu.py",
            content=(
                f"from django_toolkit.template_context.menu_entry import MenuEntry\n"
                f"{model_imports}\n"
                f"\n"
                f"def get_side_menu_items(request):\n"
                f"    menu_items = [\n"
                f"        MenuEntry(title='Home', url=('/')),\n"
                f"    ]\n"
                f"\n"
                f"    if request.user.is_superuser:\n"
                f"        menu_items.append(MenuEntry(title='Administration', is_header=True))\n"
                f"\n"
                f"    menu_items.append(MenuEntry(title='', is_header=True))\n"
                f"\n"
                f"    return menu_items\n"
            )
        )
        files.add(file) if file else None

        return files
    