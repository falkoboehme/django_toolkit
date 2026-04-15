"""
API View Creator Mixin for ModelAutoCreator
"""

from pathlib import Path
from django_toolkit.functions.files import insert_lines_in_file, create_file, is_in_file


class APIViewCreatorMixin:
    """Handles API view creation"""

    _registry: dict = {}

    def _auto_create_app_api_view(self, app_label: str) -> set:
        """Auto-create API views for a specific app. Returns a set of files if views were modified."""
        files = set()
        app_api_view_file = Path(f"{app_label}/api/views.py")

        lines = "from django.conf import settings\n"
        lines += "from rest_framework.routers import APIRootView\n"
        lines += "from rest_framework.permissions import IsAuthenticated, AllowAny\n"
        lines += "from django_toolkit.api.views import DTAPIViewSet, DTReadOnlyAPIViewSet\n"
        lines += "from .serializers import *\n"
        lines += "from ..models import *\n"

        lines += f"\n\n"
        lines += f"# RootView of App\n"
        lines += f"class {app_label.capitalize()}RootView(APIRootView):\n"
        lines += f"    \"\"\"{app_label.capitalize()} API root view\"\"\"\n"
        lines += f"    permission_classes = [IsAuthenticated] if settings.DT_LOGIN_REQUIRED else [AllowAny]\n"
        lines += f"\n"
        lines += f"    def get_view_name(self):\n"
        lines += f"        return '{app_label.capitalize()}'\n"
        lines += f"\n\n"

        lines += f"# Model ViewSets\n"

        file = create_file(
            file_path=app_api_view_file,
            content=lines,
        )
        files.add(file) if file else None

        for model_name, model_info in self._registry[app_label].items():
            model_files = self._auto_create_app_model_api_view(app_label, model_info)
            files.update(model_files) if model_files else None
        
        return files

    
    def _auto_create_app_model_api_view(self, app_label: str, model_info: dict) -> set:
        """Auto-create views for a specific model. Returns a set of files if views were modified."""
        files = set()
        app_model_view_file = Path(f"{app_label}/api/views.py")

        viewset_class_identifier = f"class {model_info['model_name']}ViewSet("
        if app_model_view_file.exists() and is_in_file(app_model_view_file, viewset_class_identifier):
            return files

        file = insert_lines_in_file(
            file_path=app_model_view_file,
            anchor="# Model ViewSets",
            lines_to_insert=self._get_model_api_view_file_content(model_info),
            check_as_block=True,
        )
        files.add(file) if file else None
        return files



    def _get_model_api_view_file_content(self, model_info: dict) -> list:
        """Generate the content for a model's view file."""
        lines = []
        model_class = model_info["model_class"]
        is_read_only = bool(getattr(model_class._meta, "read_only", False))
        base_viewset = "DTReadOnlyAPIViewSet" if is_read_only else "DTAPIViewSet"
        lines.append(f"class {model_info['model_name']}ViewSet({base_viewset}):")
        lines.append(f"    model = {model_info['model_name']}")
        lines.append(f"    serializer_class = {model_info['model_name']}Serializer")
        lines.append("")
        lines.append("")

        return lines
        



