"""
API Nested Serializer Creator Mixin for ModelAutoCreator
"""

from pathlib import Path

from django_toolkit.functions.files import create_file


class APINestedSerializerCreatorMixin:
	"""Handles API nested serializer creation"""

	_registry: dict = {}

	def _auto_create_app_api_nested_serializers(self, app_label: str) -> set:
		"""Auto-create API nested serializers for a specific app. Returns modified files."""
		files = set()
		nested_serializers_dir = Path(f"{app_label}/api/nested_serializers")

		init_file = create_file(
			file_path=nested_serializers_dir / "__init__.py",
			content=self._get_app_nested_serializer_init_content(app_label),
			overwrite=True,
		)
		files.add(init_file) if init_file else None

		for model_name, model_info in self._registry[app_label].items():
			nested_serializer_file = create_file(
				file_path=nested_serializers_dir / f"{model_name.lower()}_nested_serializer.py",
				content=self._get_model_nested_serializer_content(model_info),
				overwrite=True,
			)
			files.add(nested_serializer_file) if nested_serializer_file else None

		return files

	def _get_app_nested_serializer_init_content(self, app_label: str) -> str:
		"""Generate nested serializers package __init__ content for one app."""
		lines = []

		for model_name in sorted(self._registry[app_label].keys()):
			lines.append(
				f"from .{model_name.lower()}_nested_serializer import Nested{model_name}Serializer"
			)

		if lines:
			return "\n".join(lines) + "\n"
		return ""

	@staticmethod
	def _get_model_nested_serializer_content(model_info: dict) -> str:
		"""Generate nested serializer file content for one model."""
		model_name = model_info["model_name"]
		app_label = model_info["app_label"]
		model_class = model_info["model_class"]
		field_names = {field.name for field in model_class._meta.fields}
		nested_fields = ["'id'", "'url'", "'display'"]
		if "name" in field_names:
			nested_fields.append("'name'")

		return (
			"from rest_framework import serializers\n"
			"from django_toolkit.api.serializers import DTAPINestedSerializer\n"
			f"from ...models import {model_name}\n"
			"\n"
			"\n"
			f"class Nested{model_name}Serializer(DTAPINestedSerializer):\n"
			f"    url = serializers.HyperlinkedIdentityField(view_name='{app_label}-api:{model_name.lower()}-detail')\n"
			"\n"
			"    class Meta:\n"
			f"        model = {model_name}\n"
			f"        fields = [{', '.join(nested_fields)}]\n"
		)
