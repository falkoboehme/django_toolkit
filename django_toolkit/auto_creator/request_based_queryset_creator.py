from pathlib import Path

from ..functions.files import create_file


class RequestBasedQuerysetCreatorMixin:
    """Handles creation and synchronization of project user_based_queryset.py"""

    _registry: dict = {}
    project_name: str = ""

    def _auto_create_request_based_queryset(self) -> set:
        files = set()
        app_class_names: list[str] = []

        for app_label in sorted(self._registry.keys()):
            app_file = self._auto_create_app_request_based_queryset(app_label)
            files.add(app_file) if app_file else None
            app_class_names.append(self._get_app_queryset_class_name(app_label))

        project_file = self._auto_create_project_request_based_queryset(app_class_names)
        files.add(project_file) if project_file else None

        return files

    def _auto_create_app_request_based_queryset(self, app_label: str):
        app_file_path = f"{app_label}/request_based_queryset.py"
        app_class_name = self._get_app_queryset_class_name(app_label)

        create_file(
            file_path=app_file_path,
            content=(
                "from django_toolkit.models import RequestBasedQueryset\n"
                "\n"
                "\n"
                f"class {app_class_name}(RequestBasedQueryset):\n"
                "    pass\n"
            ),
        )

        path = Path(app_file_path)
        if not path.exists():
            return False

        content = path.read_text(encoding="utf-8")
        original_content = content

        content = self._ensure_app_class(content, app_class_name)

        model_entries = sorted(
            self._registry[app_label].values(),
            key=lambda item: item["model_class"].__name__,
        )
        for model_info in model_entries:
            model_class = model_info["model_class"]
            method_name = f"{model_class._meta.app_label}_{model_class._meta.model_name}"
            if self._method_exists(content, method_name):
                continue
            content = self._insert_method_into_app_class(content, app_class_name, method_name)

        if content != original_content:
            path.write_text(content, encoding="utf-8")
            return path.as_posix()
        return False

    def _auto_create_project_request_based_queryset(self, app_class_names: list[str]):
        project_file_path = f"{self.project_name}/request_based_queryset.py"
        imports = "\n".join(
            [
                "from django_toolkit.models import RequestBasedQueryset",
                *[
                    f"from {app_label}.request_based_queryset import {self._get_app_queryset_class_name(app_label)}"
                    for app_label in sorted(self._registry.keys())
                ],
            ]
        )

        inheritance = ",\n        ".join(app_class_names + ["RequestBasedQueryset"])
        content = (
            f"{imports}\n"
            f"\n"
            f"\n"
            f"class ProjectRequestBasedQueryset(\n"
            f"        {inheritance}\n"
            f"    ):\n"
            f"    pass\n"
        )

        path = Path(project_file_path)
        if path.exists() and path.read_text(encoding="utf-8") == content:
            return False

        create_file(
            file_path=project_file_path,
            content=content,
            overwrite=True,
        )
        return path.as_posix()


    @staticmethod
    def _get_app_queryset_class_name(app_label: str) -> str:
        parts = [part for part in app_label.replace("-", "_").split("_") if part]
        normalized = "".join(part.capitalize() for part in parts) or "App"
        return f"{normalized}RequestBasedQueryset"


    @staticmethod
    def _ensure_app_class(content: str, class_name: str) -> str:
        class_signature = f"class {class_name}(RequestBasedQueryset):"
        if class_signature in content:
            return content

        return (
            content.rstrip()
            + "\n\n\n"
            + f"class {class_name}(RequestBasedQueryset):\n"
            + "    pass\n"
        )


    @staticmethod
    def _method_exists(content: str, method_name: str) -> bool:
        return f"def {method_name}(" in content

    
    @staticmethod
    def _insert_method_into_app_class(content: str, class_name: str, method_name: str) -> str:
        class_anchor = f"class {class_name}(RequestBasedQueryset):\n"
        method_block = (
            f"\n"
            f"    def {method_name}(self, queryset, request):\n"
            f"        return self._fallback_queryset(queryset)\n"
        )

        if class_anchor not in content:
            return content

        return content.replace(class_anchor, class_anchor + method_block, 1)

    
