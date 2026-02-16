
from django_toolkit.auto_creator.auto_creator import ModelAutoCreator

def model_auto_creator(
    create_app_urls: bool = True,
    create_admin: bool = True,
    create_tables: bool = True,
    create_views: bool = True,
    create_menu_entry: bool = True,
    create_api_urls: bool = True,
    create_api_views: bool = True,
    create_api_serializers: bool = True,
):
    """Decorator to auto-register a Django model"""
    def decorator(model_class):
        options = {
            'create_app_urls': create_app_urls,
            'create_admin': create_admin,
            'create_views': create_views,
            'create_tables': create_tables,
            'create_menu_entry': create_menu_entry,
            'create_api_urls': create_api_urls,
            'create_api_views': create_api_views,
            'create_api_serializers': create_api_serializers,
        }
        ModelAutoCreator.register(model_class, **options)
        return model_class
    return decorator