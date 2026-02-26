"""
Card template context for rendering a CardDefinition.
"""
from __future__ import annotations

from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from .card_definition import CardDefinition
from .card_row import CardRow


class CardTemplate:
    """Represents one rendered card based on a CardDefinition."""

    def __init__(
        self,
        card_definition: CardDefinition,
        *,
        form=None,   # type: ignore
        instance: models.Model | None = None,
        request: HttpRequest | None = None,
        prebuilt_rows: list[CardRow] | None = None,
        ajax_js: str = "",
        template: str = "django_toolkit/includes/card.html",
        is_placeholder: bool = False,
    ):
        """
        Initialize card rendering context.

        card_definition: Card definition with `header`, `fields` and `ro_fields`.
        form: Django form for editable rows.
        instance: Model instance for display rows and read-only fallbacks.
        request: Current request, passed to `CardRow`.
        prebuilt_rows: Prebuilt rows. If set, automatic row generation is skipped.
        ajax_js: Optional inline JavaScript rendered below the card.
        template: Template path used by `render()`.

        Notes:
            - Card-level `self.read_only` is computed automatically and is `True` only
              when all configured fields are read-only.
        """
        self.header = card_definition.header or ""
        self._form = form
        self._instance = instance
        self._request = request
        self._fields = card_definition.fields or []
        self._ro_fields = card_definition.ro_fields or []
        self._rows = prebuilt_rows
        self.ajax_js = ajax_js
        self.template = template
        self.is_placeholder = is_placeholder

        if self.is_placeholder:
            self.header = ""
            self._rows = []

        self.is_read_only = bool(self._fields) and set(self._fields) == set(self._ro_fields)

    @property
    def rows(self) -> list[CardRow]:
        """Build all card rows from form or instance."""
        if self.is_placeholder:
            return []

        if self._rows is not None:
            return self._rows

        generated_rows: list[CardRow] = []
        for field_name in self._fields:
            is_read_only = field_name in self._ro_fields

            if self._form is not None and field_name in self._form.fields and not is_read_only:
                generated_rows.append(
                    CardRow(
                        bound_field=self._form[field_name],
                        request=self._request,
                    )
                )
                continue

            if self._instance is not None:
                try:
                    field = self._instance._meta.get_field(field_name)
                except FieldDoesNotExist:
                    field = None

                generated_rows.append(
                    CardRow(
                        model_instance=self._instance,
                        field=field,
                        field_name=field_name,
                        request=self._request,
                    )
                )

        return generated_rows

    def context(self) -> dict:
        """Return template context structure used by existing card views."""
        return {
            "header": self.header,
            "rows": self.rows,
            "ajax_js": self.ajax_js,
            "is_read_only": self.is_read_only,
            "is_placeholder": self.is_placeholder,
            "card": self,
            "form": self._form,
        }


    def render(self, context: dict | None = None) -> str:
        """Render card HTML from template."""
        ctx = context or {}
        ctx.update(self.context())
        return mark_safe(render_to_string(self.template, ctx))

    def __str__(self) -> str:
        return self.render()
