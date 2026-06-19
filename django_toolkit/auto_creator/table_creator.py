from typing import Dict
from pathlib import Path
from django_toolkit.functions.files import insert_line_in_file, create_file, get_app_path
from django_toolkit.functions.models import get_model_operation_name
from .functions import get_table_class_name


class TableCreatorMixin:
    """Handles table creation"""

    _registry: Dict[str, Dict] = {}

    def _auto_create_app_tables(self, app_label: str) -> set:   
        """Auto-create tables for a specific app. Returns a set of files if tables were modified."""
        files = set()
        app_base_path = get_app_path(app_label)
        app_tables_dir = app_base_path / "tables"

        # Create __init__.py if it doesn't exist
        init_file_path = app_tables_dir / "__init__.py"
        file = create_file(
            file_path=init_file_path,
            content="",
        )
        files.add(file) if file else None

        # Add Model tables
        for model_name, model_info in self._registry[app_label].items():
            if model_info.get("create_tables"):
                model_class = model_info["model_class"]
                table_class_name = get_table_class_name(model_class.__name__)
                file = create_file(
                    file_path=app_tables_dir / f"{model_name.lower()}_table.py",
                    content=self._get_model_table_file_content(model_info),
                )
                files.add(file) if file else None

                insert_line_in_file(
                    file_path=init_file_path,
                    anchor="",
                    line_to_insert=f"from .{model_name.lower()}_table import {table_class_name}",
                    position="after",
                    check_string=f"from .{model_name.lower()}_table import",
                )
        return files


    def _get_model_table_file_content(self, model_info: Dict) -> str:
        """Generate the content for a model's table file."""
        model_class = model_info["model_class"]
        lines = f"from django_toolkit.tables import DTModelTable, tables\n"
        lines += (
            f"from {model_info['app_label']}.models import {model_class.__name__}\n"
        )
        field_list = [f.name for f in model_class._meta.fields]
        view_detail = f"{model_info['app_label']}:{get_model_operation_name(model_class, 'detail')}"
        lines += f"\n\n"
        lines += f"class {get_table_class_name(model_class.__name__)}(DTModelTable):\n"
        lines += f"    class Meta(DTModelTable.Meta):\n"
        lines += f"        model = {model_class.__name__}\n"
        lines += f"        fields = {field_list}\n"
        lines += f"\n"
        lines += f"    id = tables.Column(\n"
        lines += f"        linkify={{'viewname': '{view_detail}', 'args': [tables.A('id')]}}    # type: ignore\n"
        lines += f"    )\n"
        return lines
    