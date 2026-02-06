

class ReadOnlyAdminMixin:
    """
    Mixin for Django Admin to make models completely read-only.
    
    Usage:
        @admin.register(MyModel)
        class MyModelAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
            pass
    """

    
    def has_add_permission(self, request):
        """Prevents adding new objects."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Allows only viewing, no changes."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevents deletion."""
        return False
    
    def get_readonly_fields(self, request, obj=None):
        """Makes all fields read-only."""
        return [field.name for field in self.model._meta.fields]  # Pylance: ignore [ReportAttributeAccessIssue]


class ViewOnlyAdminMixin:
    """
    Mixin for Django Admin to display models only (no changes, but navigation allowed).
    
    Usage:
        @admin.register(MyModel)
        class MyModelAdmin(ViewOnlyAdminMixin, admin.ModelAdmin):
            pass
    """
    
    def has_add_permission(self, request):
        """Prevents adding new objects."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevents deletion."""
        return False
    
    def get_readonly_fields(self, request, obj=None):
        """Makes all fields read-only."""
        return [field.name for field in self.model._meta.fields]  # Pylance: ignore [ReportAttributeAccessIssue]
