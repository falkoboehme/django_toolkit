from rest_framework.permissions import BasePermission


class DenyAll(BasePermission):
    """
    No Access, default class for REST-Framework
    """
    def has_permission(self, request, view):
        return False
    
    def has_object_permission(self, request, view, obj):
        return False
    

class IsOwner(DenyAll):
    """
    The User created this object
    """
    def has_object_permission(self, request, view, obj):
        return obj.created_user == request.user