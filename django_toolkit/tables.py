import django_tables2 as tables
from django.utils.safestring import mark_safe
from .mixins.table_pagination import EnhancedPaginator, get_paginate_count
# from .template_context.icon import icon_false, icon_true


class DTBaseTable(tables.Table):
    """
    Base table class
    """
    class Meta:
        attrs = {
            'class': 'table table-hover object-list',
        }
    
    def configure(self, request):
        """
        Configure the table for a specific request context. This performs pagination and records
        the user's preferred ordering logic.
        """
        paginate = {
            'paginator_class': EnhancedPaginator,
            'per_page': get_paginate_count(request)
        }
        tables.RequestConfig(request, paginate).configure(self)
    
    def _render_colorfield(self, value):
        return mark_safe(f'<span class="color-label" style="background-color:{value}">&nbsp;</span>')


class DTModelTable(DTBaseTable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ID (PK) column should always come first
        if 'id' in self.sequence:
            self.sequence.remove('id')
            self.sequence.insert(0, 'id')

        # Actions column should always come last
        if 'actions' in self.sequence:
            self.sequence.remove('actions')
            self.sequence.append('actions')


    def before_render(self, request):
        """
        Hook to manipulate the table
        """
        return None

    # def render_boolean_nice(self, value):
    #     return icon_true() if value else icon_false()