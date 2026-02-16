"""
URL Creator Mixin for ModelAutoCreator
"""

from ..functions.files import insert_lines_in_file, create_file
from ..functions.models import get_model_operation_alias_name
from ..functions.permissions import READ_ONLY_OPERATIONS, ALL_OPERATIONS
from .functions import get_comment_header, get_view_class_name


class URLCreatorMixin:
    """Handles URL creation and synchronization"""

    _registry: dict = {}
    project_name: str = ""

    def _auto_create_project_urls(self) -> set:
        """Auto-sync URLs for all registered models. Returns list of modified files."""
        files = set()
        project_urls_path = f"{self.project_name}/urls.py"

        # Insert import statements
        import_lines = [
            "from django.urls import path, include",
            "from django_toolkit.views import HomeView, UserLoginView, UserLogoutView",
        ]
        file = insert_lines_in_file(
            file_path=project_urls_path,
            anchor="from django.urls import path",
            lines_to_insert=import_lines,
            position="after",
        )
        files.add(file) if file else None

        # Insert app URL includes
        for app_label, models in self._registry.items():
            file = insert_lines_in_file(
                file_path=project_urls_path,
                anchor="urlpatterns = [",
                lines_to_insert=[
                    f"    path('{app_label}/', include('{app_label}.urls')),"
                ],
            )
            files.add(file) if file else None

        header_user_apps = get_comment_header("User Apps")
        file = insert_lines_in_file(
            file_path=project_urls_path,
            anchor="urlpatterns = [",
            lines_to_insert=[f"    {header_user_apps}"],
        )
        files.add(file) if file else None

        # Insert basic URL patterns if not present
        header_basics = get_comment_header("Basics")
        lines = [
            f"    {header_basics}",
            f"    path('', HomeView.as_view(), name='home'),",
            f"    path('login', UserLoginView.as_view(), name='login'),",
            f"    path('logout', UserLogoutView.as_view(), name='logout'),",
        ]
        file = insert_lines_in_file(
            file_path=project_urls_path,
            anchor="urlpatterns = [",
            lines_to_insert=lines,
        )
        files.add(file) if file else None

        return files


    def _auto_create_app_urls(self, app_label: str) -> set:
        """Auto-sync URLs for a specific app. Returns True if URLs were modified."""
        files = set()
        app_urls_path = f"{app_label}/urls.py"

        # Create urls.py if it doesn't exist
        file = create_file(
            file_path=app_urls_path,
            content=(
                f"from django.urls import path\n"
                f"from . import views\n"
                f"\n"
                f"app_name = '{app_label}'\n"
                f"urlpatterns = [\n"
                f"]"
            ),
        )
        files.add(file) if file else None

        # Add Model endpoint imports
        for model_name, model_info in self._registry[app_label].items():
            if model_info.get("create_app_urls"):
                file = insert_lines_in_file(
                    file_path=app_urls_path,
                    anchor="urlpatterns = [",
                    lines_to_insert=self._get_model_url_paths(model_info),
                    check_as_block=True,
                    skip_if_any_exists=True,
                )
                files.add(file) if file else None
        return files


    def _get_model_url_paths(self, model_info: dict) -> list:
        """Generate URL paths for a model"""
        lines = []
        model_class = model_info["model_class"]
        header = get_comment_header(model_class.__name__)

        lines.append(f"    {header}\n")
        view_types = (
            READ_ONLY_OPERATIONS if model_class._meta.read_only else ALL_OPERATIONS
        )

        for view_type in view_types:
            url_pattern = self._get_url_pattern(model_class.__name__, view_type)
            view_name = get_view_class_name(model_class.__name__, view_type)
            url_name = get_model_operation_alias_name(model_class.__name__, view_type)
            lines.append(
                f"    path('{url_pattern}', views.{view_name}.as_view(), name='{url_name}'),"
            )

        return lines

    @staticmethod
    def _get_url_pattern(model_name: str, view_type: str) -> str:
        """Create a URL pattern based on model name and view type"""
        assert view_type in ALL_OPERATIONS, "Invalid view type"

        if view_type == "list":
            return f"{model_name.lower()}s/"
        elif view_type == "add":
            return f"{model_name.lower()}s/{view_type}/"
        elif view_type == "detail":
            return f"{model_name.lower()}s/<int:pk>/"
        elif view_type in ["change", "delete"]:
            return f"{model_name.lower()}s/<int:pk>/{view_type}/"
        return ""
