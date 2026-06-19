"""
Admin Creator Mixin for ModelAutoCreator
"""

from typing import Dict
from pathlib import Path

from ..functions.files import create_file, insert_line_in_file, get_app_path


class AdminCreatorMixin:
    """Handles admin creation"""

    _registry: Dict[str, Dict] = {}
    
    def _auto_create_admin(self, app_label: str) -> set:
        """Auto-create admin.py for a specific app. Returns a set of modified files."""
        files = set()
        app_base_path = get_app_path(app_label)
        admin_path = app_base_path / "admin.py"

        file = create_file(
            file_path=admin_path,
            content=(
                "from django.contrib import admin\n"
                "from .models import *\n"
                "\n"
                "# Register your models here.\n"
            ),
        )
        files.add(file) if file else None

        file = insert_line_in_file(
            file_path=admin_path,
            anchor="from django.contrib import admin",
            line_to_insert="from .models import *",
            position="after",
            check_string="from .models import",
        )
        files.add(file) if file else None

        for model_info in self._registry.get(app_label, {}).values():
            if not model_info.get("create_admin", True):
                continue

            model_class = model_info["model_class"]
            model_name = model_class.__name__
            register_line = f"admin.site.register({model_name})"

            if self._is_model_already_registered(admin_path, model_name):
                continue

            file = self._insert_admin_register_line(admin_path, register_line)
            files.add(file) if file else None

        return files


    @staticmethod
    def _insert_admin_register_line(admin_path, register_line: str):
        anchors = [
            "# Register your models here.",
            "from .models import *",
            "from django.contrib import admin",
        ]
        for anchor in anchors:
            file = insert_line_in_file(
                file_path=admin_path,
                anchor=anchor,
                line_to_insert=register_line,
                position="after",
                check_string=register_line,
            )
            if file:
                return file
        return False


    @staticmethod
    def _is_model_already_registered(admin_path, model_name: str) -> bool:
        path = Path(admin_path)
        if not path.exists():
            return False

        content = path.read_text(encoding="utf-8")
        patterns = [
            f"admin.site.register({model_name})",
            f"@admin.register({model_name})",
            f"admin.site.register(({model_name},",
            f"admin.site.register([{model_name},",
        ]
        return any(pattern in content for pattern in patterns)
