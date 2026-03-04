"""
Django Toolkit App Configuration
"""
from django.apps import AppConfig
import os
import logging


log = logging.getLogger("toolkit")

class DjangoToolkitConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_toolkit'
    
    def ready(self):
        """
        Called when Django starts and all apps are loaded.
        Auto-syncs URLs for all registered models.
        """
        # Only run in main process, not in reloader
        if os.environ.get('RUN_MAIN') != 'true':
            return
        
        from django.conf import settings
        from django.apps import apps
        from .auto_creator.auto_creator import DTModelAutoCreator
        
        # Only auto-sync in DEBUG mode
        if not settings.DEBUG:
            return
        
        # Ensure all models are loaded
        apps.get_models()
        
        # print("🔍 django_toolkit: Auto-syncing URLs for registered models...")
        # print(f"   Registered apps: {list(ModelAutoCreator._registry.keys())}")
        # for app_label, models in ModelAutoCreator._registry.items():
        #     print(f"   {app_label}: {list(models.keys())}")
        try:
            # Auto-sync URLs
            modified_files = DTModelAutoCreator().auto_create()
            
            if modified_files:
                log.info("URLs were auto-updated")
                for file in modified_files:
                    log.info(f"Updated: {file}")
                log.info("Django will restart automatically")
                
                # Trigger Django reload by touching manage.py
                from pathlib import Path
                manage_py = Path(settings.BASE_DIR) / 'manage.py'
                if manage_py.exists():
                    manage_py.touch()
        except Exception as e:
            log.exception(f"django_toolkit auto-sync failed: {e}")

