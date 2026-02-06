from django.conf import settings
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from django.contrib import auth
from django.contrib.auth.models import Permission


import logging
log = logging.getLogger("dt.permissions")


def permissions_by_model(permission_list):
    codename_mapping = {
        'add': 'a',
        'change': 'c',
        'delete': 'd',
        'view': 'v',
    }
    
    display_dict = {}
    for permission in permission_list:
        permission_model = permission.content_type.model_class()
        if not permission_model in display_dict:
            display_dict[permission_model] = []
        permission_opereration = (permission.codename).split('_')[0]
        short_op = codename_mapping[permission_opereration]
        display_dict[permission_model].append(short_op)
    return display_dict


def permission_to_string(permisson):
    """
    Returns the text of the permission (<Permission: Inventory | Cloudarea | Can add Cloudarea> -> inventory.add_cloudarea)
    """
    return f"{permisson.content_type.app_label}.{permisson.codename}"


def string_to_permission(permission_str):
    """
    Returns the permission object from the permission_str (e.g. auth.view_group)
    """
    app_label, codename = permission_str.split(".", 1)
    return Permission.objects.get(content_type__app_label=app_label, codename=codename)


def build_permission_for_model_operation(model, operation):
    return f"{model._meta.app_label}.{operation}_{model._meta.model_name}"


def get_permission_for_model(model, action):
    """
    Resolve the named permission for a given model (or instance) and action (e.g. view or add).

    :param model: A model or instance
    :param action: View, add, change, or delete (string)
    """
    # Resolve to the "concrete" model (for proxy models)
    model = model._meta.concrete_model

    return f'{model._meta.app_label}.{action}_{model._meta.model_name}'


# A few helper functions for common logic between User and AnonymousUser.
def user_get_permissions(user, obj, from_name):
    permissions = set()
    name = "get_%s_permissions" % from_name
    for backend in auth.get_backends():
        if hasattr(backend, name):
            func = getattr(backend, name)
            permissions.update(func(user, obj))
    return permissions


def user_has_perm(user, perm, obj):
    """
    A backend can raise `PermissionDenied` to short-circuit permission checking.
    """
    for backend in auth.get_backends():
        if not hasattr(backend, "has_perm"):
            continue
        try:
            if backend.has_perm(user, perm, obj):
                return True
        except PermissionDenied:
            return False
    return False


def user_has_module_perms(user, app_label):
    """
    A backend can raise `PermissionDenied` to short-circuit permission checking.
    """
    for backend in auth.get_backends():
        if not hasattr(backend, "has_module_perms"):
            continue
        try:
            if backend.has_module_perms(user, app_label):
                return True
        except PermissionDenied:
            return False
    return False


def is_owner(user, obj):
    """
    Is the given user owner of the object (created_user)
    """

    if hasattr(obj, 'created_user'):
        username_field = getattr(user, settings.USERNAME_FIELD)
        if obj.created_user == username_field:
            return True

    return False


def user_has_object_perms(user, obj, operation=None):
    """
    Check if a user has permissions to [view, change, delete, add] an object.
    For add, obj must be the model.
    """
    # TODO
    all_operations = ['view', 'add', 'change', 'delete']
    if operation not in all_operations:
        raise ImproperlyConfigured(f"operation must be in {all_operations}. Not {operation}")
    all_user_permissions = user.get_all_permissions()
    
    # for add we do not have an object, so model permissions to add are sufficiant
    if operation == "add":
        req_perm = get_permission_for_model(model=obj, action=operation)
        if req_perm in all_user_permissions:
            return True
    else:
        model = obj._meta.model
        req_perm = get_permission_for_model(model=model, action=operation)
        # Check model permission
        if req_perm in all_user_permissions:
            # Check object permission
            pass
    return False

    

def raise_permission_denied(user, model_obj, action):
    if action == 'add':
        log.error(f"User '{user}' does not have the permission to {action} objects to model '{model_obj}'")
        raise PermissionDenied(f"You do not have permission to {action} data.")
    else:
        log.error(f"User '{user}' does not have the permission to {action} object '{model_obj}'")
        raise PermissionDenied(f"You do not have permission to {action} this data.")




