"""
View Creator Mixin for ModelAutoCreator
"""

from typing import Dict
from pathlib import Path
from django_toolkit.functions.files import insert_line_in_file, create_file, get_app_path
from django_toolkit.functions.permissions import READ_ONLY_OPERATIONS, ALL_OPERATIONS
from .functions import get_view_class_name, get_base_view_class, get_table_class_name


class ViewCreatorMixin:
    """Handles view creation"""

    _registry: Dict[str, Dict] = {}

    def _auto_create_app_views(self, app_label: str) -> set:
        """Auto-create views for a specific app. Returns a set of files if views were modified."""
        files = set()
        app_base_path = get_app_path(app_label)
        app_views_dir = app_base_path / "views"

        # Create __init__.py if it doesn't exist
        init_file_path = app_views_dir / "__init__.py"
        file = create_file(
            file_path=init_file_path,
            content="",
        )
        files.add(file) if file else None

        # Add Model views
        for model_name, model_info in self._registry[app_label].items():
            if model_info.get("create_views"):
                view_class_name = get_view_class_name(model_name, "list")
                file = create_file(
                    file_path=app_views_dir / f"{model_name.lower()}_views.py",
                    content=self._get_model_view_file_content(model_info),
                )
                files.add(file) if file else None

                insert_line_in_file(
                    file_path=init_file_path,
                    anchor="",
                    line_to_insert=f"from .{model_name.lower()}_views import *",
                    position="after",
                    check_string=f"from .{model_name.lower()}_views import *",
                )
        return files

    
    def _get_model_view_file_content(self, model_info: Dict) -> str:
        """Generate the content for a model's view file."""
        lines = ""
        model_class = model_info["model_class"]
        is_read_only = bool(getattr(model_class._meta, "read_only", False))

        if is_read_only:
            view_types = READ_ONLY_OPERATIONS
            lines += f"from django_toolkit.views import DTListView, DTDetailView\n"
        else:
            view_types = ALL_OPERATIONS
            lines += f"from django_toolkit.views import DTListView, DTDetailView, DTCreateView, DTUpdateView, DTDeleteView\n"
            lines += f"from django_toolkit.functions.models import get_app_model_url, get_fields_of_model\n"

        lines += (
            f"from {model_info['app_label']}.models import {model_class.__name__}\n"
        )
        lines += f"from {model_info['app_label']}.tables import {get_table_class_name(model_class.__name__)}\n"
        for view_type in view_types:
            view_name = get_view_class_name(model_class.__name__, view_type)
            lines += f"\n\n"
            lines += f"class {view_name}({get_base_view_class(view_type)}):\n"
            lines += f"    model = {model_class.__name__}\n"
            if view_type == "list":
                lines += f"    table_class = {model_class.__name__}Table\n"
            if view_type in ["create", "update", "delete"]:
                lines += (
                    f"    success_url = get_app_model_url({model_class.__name__})\n"
                )
            if view_type in ["create", "update"]:
                lines += (
                    f"    fields = get_fields_of_model({model_class.__name__}, 'rw')\n"
                )

        return lines
