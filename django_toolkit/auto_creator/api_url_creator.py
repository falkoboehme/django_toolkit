"""
API URL Creator Mixin for ModelAutoCreator
"""

from pathlib import Path
from ..functions.files import insert_lines_in_file, insert_line_in_file, create_file, get_app_path
from ..functions.models import get_model_base_url
from .functions import get_comment_header

class APIURLCreatorMixin:
    """Handles URL creation and synchronization"""

    _registry: dict = {}
    project_name: str = ""

    def _auto_create_project_api_urls(self) -> set:
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

        api_import_lines = [
            "from django_toolkit.api.views import APIRootView, DocsView",
            "from django_toolkit.api.swagger import schema_view",
            "from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView",
        ]
        file = insert_lines_in_file(
            file_path=project_urls_path,
            anchor="from django_toolkit.views import HomeView, UserLoginView, UserLogoutView",
            lines_to_insert=api_import_lines,
            position="after",
        )
        files.add(file) if file else None

        # Insert API basics + docs routes
        api_basics_lines = [
            f"    {get_comment_header('API Basics')}",
            "    path('api/', APIRootView.as_view(), name='api-root'),",
            "    path('api/docs/', DocsView.as_view(), name='api-docs'),",
            f"    {get_comment_header('API Swagger v2')}",
            "    path('api/docs/swagger-v2/', schema_view.with_ui('swagger', cache_timeout=86400), name='api-swagger-v2'),",
            f"    {get_comment_header('API Swagger v3')}",
            "    path('api/docs/swagger-v3/', SpectacularSwaggerView.as_view(url_name='api-swagger-v3-download'), name='api-swagger-v3'),",
            "    path('api/docs/swagger-v3/download/', SpectacularAPIView.as_view(), name='api-swagger-v3-download'),",
            "    path('api/docs/swagger-v3/redoc/', SpectacularRedocView.as_view(url_name='api-swagger-v3-download'), name='api-swagger-v3-redoc'),",
        ]
        file = insert_lines_in_file(
            file_path=project_urls_path,
            anchor="urlpatterns = [",
            lines_to_insert=api_basics_lines,
            check_as_block=True,
        )
        files.add(file) if file else None

        # Insert app URL includes
        for app_label, models in self._registry.items():
            include_line = f"    path('api/{app_label}/', include('{app_label}.api.urls'))," 
            file = insert_line_in_file(
                file_path=project_urls_path,
                anchor="urlpatterns = [",
                line_to_insert=include_line,
                check_string=f"path('api/{app_label}/', include('{app_label}.api.urls'))",
            )
            files.add(file) if file else None

        header_user_apps = get_comment_header("API User Apps")
        file = insert_line_in_file(
            file_path=project_urls_path,
            anchor="urlpatterns = [",
            line_to_insert=f"    {header_user_apps}",
            check_string=f"    {header_user_apps}",
        )
        files.add(file) if file else None



        return files


    def _auto_create_app_api_urls(self, app_label: str) -> set:
        """Auto-sync URLs for a specific app. Returns True if URLs were modified."""
        files = set()
        app_base_path = get_app_path(app_label)
        app_api_dir = app_base_path / "api"
        app_api_urls_path = app_api_dir / "urls.py"

        # Ensure api package exists
        file = create_file(
            file_path=app_api_dir / "__init__.py",
            content="",
        )
        files.add(file) if file else None

        # Create urls.py if it doesn't exist
        file = create_file(
            file_path=app_api_urls_path,
            content=(
                f"from django_toolkit.api.routers import DTRouter\n"
                f"from .views import *\n"
                f"\n"
                f"router = DTRouter()\n"
                f"router.APIRootView = {app_label.capitalize()}RootView\n"
                f"app_name = '{app_label}-api'\n"
                f"\n"
                f"urlpatterns = router.urls"
            ),
        )
        files.add(file) if file else None

        # Add Model endpoint imports
        for model_name, model_info in self._registry[app_label].items():
            if model_info.get("create_api_urls"):
                base_url = get_model_base_url(model_info["model_class"])
                file = insert_line_in_file(
                    file_path=app_api_urls_path,
                    anchor="urlpatterns = router.urls",
                    line_to_insert=f"router.register('{base_url}', {model_name}ViewSet, basename='{base_url}')",
                    check_string=f"basename='{base_url}'",
                    position="before",
                )
                files.add(file) if file else None
        return files
