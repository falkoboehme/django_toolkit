"""
Django Toolkit App Configuration
"""
from django.apps import AppConfig
import os

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
        from .auto_creator.auto_creator import ModelAutoCreator
        
        # Only auto-sync in DEBUG mode
        if not settings.DEBUG:
            return
        
        # Ensure all models are loaded
        apps.get_models()
        
        print("🔍 django_toolkit: Auto-syncing URLs for registered models...")
        print(f"   Registered apps: {list(ModelAutoCreator._registry.keys())}")
        for app_label, models in ModelAutoCreator._registry.items():
            print(f"   {app_label}: {list(models.keys())}")
        try:
            # Auto-sync URLs
            modified_files = ModelAutoCreator().auto_sync()
            
            if modified_files:
                print("\n" + "="*60)
                print("🔄 django_toolkit: URLs were auto-updated")
                for file in modified_files:
                    print(f"   Updated: {file}")
                print("   Django will restart automatically...")
                print("="*60 + "\n")
                
                # Trigger Django reload by touching manage.py
                from pathlib import Path
                manage_py = Path(settings.BASE_DIR) / 'manage.py'
                if manage_py.exists():
                    manage_py.touch()
        except Exception as e:
            print(f"⚠ django_toolkit auto-sync failed: {e}")
            import traceback
            traceback.print_exc()

