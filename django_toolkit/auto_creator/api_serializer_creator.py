"""
API Serializer Creator Mixin for ModelAutoCreator
"""

from pathlib import Path

from django_toolkit.functions.files import create_file, get_app_path
from django_toolkit.functions.models import get_model_base_url


class APISerializerCreatorMixin:
	"""Handles API serializer creation"""

	_registry: dict = {}

	def _auto_create_app_api_serializers(self, app_label: str) -> set:
		"""Auto-create API serializers for a specific app. Returns modified files."""
		files = set()
		app_base_path = get_app_path(app_label)
		serializers_dir = app_base_path / "api" / "serializers"

		init_file = create_file(
			file_path=serializers_dir / "__init__.py",
			content=self._get_app_serializer_init_content(app_label),
			overwrite=True,
		)
		files.add(init_file) if init_file else None

		for model_name, model_info in self._registry[app_label].items():
			serializer_file = create_file(
				file_path=serializers_dir / f"{model_name.lower()}_serializer.py",
				content=self._get_model_serializer_content(model_info),
				overwrite=False,
			)
			files.add(serializer_file) if serializer_file else None

		return files

	def _get_app_serializer_init_content(self, app_label: str) -> str:
		"""Generate serializers package __init__ content for one app."""
		lines = []

		for model_name in sorted(self._registry[app_label].keys()):
			lines.append(
				f"from .{model_name.lower()}_serializer import {model_name}Serializer"
			)

		if lines:
			return "\n".join(lines) + "\n"
		return ""

	@staticmethod
	def _get_model_serializer_content(model_info: dict) -> str:
		"""Generate serializer file content for one model."""
		model_name = model_info["model_name"]
		app_label = model_info["app_label"]
		model_class = model_info["model_class"]
		base_url = get_model_base_url(model_class)
		is_read_only = bool(getattr(model_class._meta, "read_only", False))
		read_only_fields_line = ""
		if is_read_only:
			read_only_fields_line = (
				f"        read_only_fields = tuple(field.name for field in [*{model_name}._meta.fields, *{model_name}._meta.many_to_many])\n"
			)
		return (
			"from rest_framework import serializers\n"
			"from django_toolkit.api.serializers import DTAPISerializer\n"
			f"from ...models import {model_name}\n"
			"\n"
			"\n"
			f"class {model_name}Serializer(DTAPISerializer):\n"
			f"    url = serializers.HyperlinkedIdentityField(view_name='{app_label}-api:{base_url}-detail')\n"
			"\n"
			"    class Meta(DTAPISerializer.Meta):\n"
			f"        model = {model_name}\n"
			"        fields = ('__all__')\n"
			f"{read_only_fields_line}"
		)
