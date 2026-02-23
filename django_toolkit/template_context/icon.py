import re
from pathlib import Path
from django.conf import settings
from django.utils.safestring import mark_safe


def icon_false(width=16, height=16, fillcolor='red'):
    return mark_safe(
        SVGIcon(icon_name="close-thick", title="False", width=width, height=height, fillcolor=fillcolor).html
    )


def icon_true(width=16, height=16, fillcolor='green'):
    return mark_safe(
        SVGIcon(icon_name="check-bold", title="True", width=width, height=height, fillcolor=fillcolor).html
    )


def icon_rest_api(width=32, height=32, fillcolor='blue'):
    return mark_safe(
        SVGIcon(icon_name="rest-api", title="REST API", url="/api/", width=width, height=height, fillcolor=fillcolor).html
    )


def icon_swagger_v2(width=32, height=32, fillcolor='blue'):
    return mark_safe(
        SVGIcon(icon_name="swagger", title="Swagger API v2", url="/api/docs/swagger-v2/", width=width, height=height, fillcolor=fillcolor).html
    )


def icon_swagger_v3(width=32, height=32, fillcolor='blue'):
    return mark_safe(
        SVGIcon(icon_name="swagger", title="Swagger API v3", url="/api/docs/swagger-v3/", width=width, height=height, fillcolor=fillcolor).html
    )



class SVGIcon:
    def __init__(
            self,
            icon_name,
            title=None,
            fillcolor=None,
            width=16,
            height=16,
            viewbox=None,
            url=None,
        ):
        self.icon_name = icon_name if icon_name.endswith(".svg") else f"{icon_name}.svg"
        self.title = title
        self.fillcolor = fillcolor
        self.width = width
        self.height = height
        self.viewbox = viewbox
        self.url = url
        self.html = self.get_html()


    def get_html(self):
        tags = self._extract_tags()
        if tags:
            title = f'<title>{self.title}</title>' if self.title else ''
            viewbox = self.viewbox if self.viewbox else tags['viewbox']
            if self.url:
                return  f'<a href="{self.url}">' \
                        f"<svg width=\"{self.width}px\" height=\"{self.height}px\" viewBox=\"{viewbox}\">{title}<path fill=\"{self.fillcolor}\" d=\"{tags['d']}\" /></svg>" \
                        f'</a>'
            else:
                return f"<svg width=\"{self.width}px\" height=\"{self.height}px\" viewBox=\"{viewbox}\">{title}<path fill=\"{self.fillcolor}\" d=\"{tags['d']}\" /></svg>"
        else:
            return f"{self.icon_name} not found"
    

    def _extract_tags(self):
        icon_file = Path.joinpath(settings.STATIC_ROOT, "django_toolkit", "icons", self.icon_name)
        try:
            with open(icon_file, 'r', encoding='utf-8') as file:
                file_content = file.read()
            return {
                'd': re.findall(r' d="(.*?)"', file_content)[0],
                'viewbox': re.findall(r' viewBox="(.*?)"', file_content)[0],
            }
        except FileNotFoundError as error:
            return False