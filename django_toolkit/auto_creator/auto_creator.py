"""
Auto-Registration System for Django Models

Automatically registers models and generates URLs/Views/Admin
"""
from django.conf import settings
from django.db import models
from django_toolkit.functions.files import get_project_name
from .api_url_creator import APIURLCreatorMixin
from .api_serializer_creator import APISerializerCreatorMixin
from .api_nested_serializer_creator import APINestedSerializerCreatorMixin
from .api_view_creator import APIViewCreatorMixin

from .url_creator import URLCreatorMixin
from .view_creator import ViewCreatorMixin
from .table_creator import TableCreatorMixin
from .admin_creator import AdminCreatorMixin
from .settings_creator import SettingsCreatorMixin
from .request_based_queryset_creator import RequestBasedQuerysetCreatorMixin
from.menu_creator import MenuCreator

from django_toolkit.functions.debug import *

class DTModelAutoCreator(
    SettingsCreatorMixin,
    URLCreatorMixin,
    ViewCreatorMixin,
    TableCreatorMixin,
    AdminCreatorMixin,
    RequestBasedQuerysetCreatorMixin,
    MenuCreator,
    APIURLCreatorMixin,
    APISerializerCreatorMixin,
    APINestedSerializerCreatorMixin,
    APIViewCreatorMixin,
):
    """Central registry for auto-registered models with automatic URL synchronization"""
    
    _registry: dict = {}

    read_write_actions = ['Add', 'Edit', 'Delete']
    read_only_actions = ['List', 'Detail']

    @classmethod
    def register(cls,
        model_class: models.Model,
        **kwargs
    ) -> models.Model:
        """Register a model with optional configuration"""
        app_label = model_class._meta.app_label
        model_name = model_class.__name__
        
        cls._registry.setdefault(app_label, {})[model_name] = {
            'app_label': app_label,
            'model_class': model_class,
            'model_name': model_name,
            **kwargs
        }
        return model_class
    

    def auto_create(self) -> set:
        """Automatically create URLs, Views, Admin, etc. for all registered models. Returns list of modified files."""
        all_files = set()
        self.project_name = get_project_name()
        if not self.project_name:
            raise Exception("Could not determine project name for auto-syncing URLs")
       
        # Auto-create settings (if needed)
        # all_files.update(self._auto_create_stettings())

        # Auto-create project request_based_queryset.py (if needed)
        all_files.update(self._auto_create_request_based_queryset())
        
        if settings.DT_AUTO_CREATE_MENU:
            # Auto-create Menu (if needed)
            all_files.update(self._auto_create_menu())

        if settings.DT_AUTO_CREATE_VIEWS:
            # Auto-create Tables for each app
            for app_label in self._registry:
                files = self._auto_create_app_tables(app_label)
                all_files.update(files) if files else None

            # Auto-create Views for each app
            for app_label in self._registry:
                files = self._auto_create_app_views(app_label)
                all_files.update(files) if files else None

            # Auto-create URLs for each app
            for app_label in self._registry:
                files = self._auto_create_app_urls(app_label)
                all_files.update(files) if files else None
            
            # Auto-create project-level URLs
            all_files.update(self._auto_create_project_urls())

        if settings.DT_AUTO_CREATE_ADMIN_AREA:
            # Auto-create Admin for each app
            for app_label in self._registry:
                files = self._auto_create_admin(app_label)
                all_files.update(files) if files else None

        if settings.DT_AUTO_CREATE_API:
            # Auto-create API URLs for each app
            for app_label in self._registry:
                files = self._auto_create_app_api_urls(app_label)
                all_files.update(files) if files else None

            # Auto-create API serializers for each app
            for app_label in self._registry:
                files = self._auto_create_app_api_serializers(app_label)
                all_files.update(files) if files else None

            # Auto-create API nested serializers for each app
            for app_label in self._registry:
                files = self._auto_create_app_api_nested_serializers(app_label)
                all_files.update(files) if files else None

            # Auto-create API views for each app
            for app_label in self._registry:
                files = self._auto_create_app_api_view(app_label)
                all_files.update(files) if files else None
        
            # Auto-create project-level API URLs
            all_files.update(self._auto_create_project_api_urls())
        
        return all_files
    