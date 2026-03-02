from django.conf import settings

from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from drf_yasg.generators import OpenAPISchemaGenerator

# allows HTTP- or HTTPS-requests from swagger
class BothHttpAndHttpsSchemaGenerator(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        schema.schemes = ["http", "https"]
        return schema


openapi_info = openapi.Info(
    title=settings.DJANGO_FAST_DEV_PROJECT_NAME,
    default_version=settings.DJANGO_FAST_DEV_PROJECT_VERSION,
    description=settings.DJANGO_FAST_DEV_PROJECT_DESCRIPTION,
    license=openapi.License(name="Apache v2 License"),
)

schema_view = get_schema_view(
    openapi_info,
    validators=['flex', 'ssv'],
    public=True,
    permission_classes=(),
    generator_class=BothHttpAndHttpsSchemaGenerator,
)