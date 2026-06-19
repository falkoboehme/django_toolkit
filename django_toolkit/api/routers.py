from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns

class DTRouter(DefaultRouter):
    # Extend DRF's built-in DefaultRouter to alphabetically order endpoints under the root view

    def get_api_root_view(self, api_urls=None):
        api_root_dict = {}
        list_name = self.routes[0].name
        for prefix, viewset, basename in sorted(self.registry, key=lambda x: x[0]):
            api_root_dict[prefix] = list_name.format(basename=basename)

        return self.APIRootView.as_view(api_root_dict=api_root_dict)

    def get_urls(self):
        urls = super(DefaultRouter, self).get_urls()

        if self.include_root_view:
            view = self.get_api_root_view(api_urls=urls)
            root_url = path('', view, name=self.root_view_name)
            urls.append(root_url)

        if self.include_format_suffixes:
            try:
                urls = format_suffix_patterns(urls)
            except ValueError as exc:
                if "Converter 'drf_format_suffix' is already registered." not in str(exc):
                    raise

        return urls
