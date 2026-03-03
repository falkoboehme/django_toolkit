from django.conf import settings
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from rest_framework.serializers import ValidationError


import logging
log = logging.getLogger("auth")


__all__ = ['CheckPermissionMixin']


class CheckPermissionMixin:
    """
    Checks if the user has the permission to perform the action
    """

    METHOD_PERMISSION_MAPPING = {
        "GET": "view",
        "POST": "add",
        "PUT": "change",
        "PATCH": "change",
        "DELETE": "delete",
    }

    def _check_perm(self, perm_list, request, model):
        for permission in perm_list:
            permission_app = permission.content_type.app_label
            if permission_app == model._meta.app_label:
                if permission.codename == f"{self.METHOD_PERMISSION_MAPPING[request.method]}_{model.__name__.lower()}":
                    return True
        return False

    
    def check_user_model_permissions(self, request):
        """
        Checks if a user has the rights to perform the action
        """

        model = None
        # Is a model defined in the serializer?
        if hasattr(self.serializer_class, "Meta"):              # type: ignore
            if hasattr(self.serializer_class.Meta, "model"):    # type: ignore
                model = self.serializer_class.Meta.model        # type: ignore
        
        # If no model is defined, does the serializer has a get_serializer_class method?
        if model is None:
            if hasattr(self, "get_serializer_class") and callable(getattr(self, 'get_serializer_class')):
                serializer_class = self.get_serializer_class()  # type: ignore
                model = serializer_class.Meta.model        
                
        if model is None:
            raise ValidationError(
                f"serializer_class of '{self.serializer_class}' not defined in check_user_model_permissions"    # type: ignore
            )
        
        model_app = model._meta.app_label

        # Is the user allowed?
        user_permissions = Permission.objects.filter(user=request.user)
        group_permissions = Permission.objects.filter(group__user=request.user)
        if self._check_perm(user_permissions, request, model):
            return True
        if self._check_perm(group_permissions, request, model):
            return True
                
        # User is not allowed, log the request
        requested_uri = request.build_absolute_uri()
        log.warning(f"{request.method} on {requested_uri} denied for '{request.user}'")
        raise PermissionDenied(
            f"You do not have permission to perform a {request.method}-request on {model_app}/{model.__name__.lower()}."
        )


    # GET (list all/multiple objects)
    def list(self, request, *args, **kwargs):
        self.check_user_model_permissions(request)
        return super().list(request, *args, **kwargs)       # type: ignore
    

    # GET (get only one object)
    def retrieve(self, request, *args, **kwargs):
        self.check_user_model_permissions(request)
        return super().retrieve(request, *args, **kwargs)       # type: ignore


    # POST (create an object)
    def create(self, request, *args, **kwargs):
        self.check_user_model_permissions(request)
        return super().create(request, *args, **kwargs)       # type: ignore


    # PUT (change the whole object)
    def update(self, request, *args, **kwargs):
        self.check_user_model_permissions(request)
        return super().update(request, *args, **kwargs)     # type: ignore
    

    # PATCH (change only some fields)
    def partial_update(self, request, *args, **kwargs):
        self.check_user_model_permissions(request)
        return super().partial_update(request, *args, **kwargs)     # type: ignore


    # DELETE (delete an object)
    def destroy(self, request, *args, **kwargs):
        self.check_user_model_permissions(request)
        return super().destroy(request, *args, **kwargs)        # type: ignore
