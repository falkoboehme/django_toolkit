from django.conf import settings
from django.db import models
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from django.contrib import auth
from django.contrib.auth.models import Permission

import logging
log = logging.getLogger("toolkit")

"""
This module contains functions to check permissions for users and objects.

Permissions are defined in the Django auth system and can be assigned to users and groups.
The main function is `user_has_object_perms` which checks if a user has the required permissions to perform an action on an object.

Permissions can be represented as strings (e.g. "auth.view_group") or as Permission objects.
The functions in this module can handle both representations.

In general we use the "app_label.action_modelname" format for permission (e.g. "auth.view_group"),
because we need no database query to check if a user has a permission, while if we use Permission objects,
we need to query the database to get the Permission object for the string representation of the permission.

If we receive a permission object, we convert it to a string using the `permission_to_string` function.
If you need an  permission object from a string, you can use the `string_to_permission` function,
but be aware that this will query the database, so it should be used with caution.

"""


READ_ONLY_OPERATIONS = ["list", "detail"]
READ_WRITE_OPERATIONS = ["create", "update", "delete"]
ALL_OPERATIONS = READ_ONLY_OPERATIONS + READ_WRITE_OPERATIONS

PERMISSION_ACTION = ["view", "add", "change", "delete"]
OPERATION_PERMISSION_ACTION_MAPPING = {
    "detail": "view",
    "list": "view",
    "create": "add",
    "update": "change",
    "delete": "delete",
}


def get_perm_action_from_operation(operation):
    if operation in OPERATION_PERMISSION_ACTION_MAPPING:
        return OPERATION_PERMISSION_ACTION_MAPPING[operation]
    else:
        raise ImproperlyConfigured(
            f"Operation '{operation}' is not supported. Supported operations are: {ALL_OPERATIONS}"
        )


def get_operations_from_perm_action(perm_action):
    if perm_action in OPERATION_PERMISSION_ACTION_MAPPING.values():
        return [
            operation
            for operation, pa in OPERATION_PERMISSION_ACTION_MAPPING.items()
            if pa == perm_action
        ]
    else:
        raise ImproperlyConfigured(
            f"Permission action '{perm_action}' is not supported. Supported permission actions are: {PERMISSION_ACTION}"
        )


def permission_to_string(permission_obj: Permission) -> str:
    """
    Returns the string of the permission (<Permission: Auth | Group | Can add Group> -> auth.add_group)
    permission_obj can be a Permission object, a list of Permission objects or a QuerySet of Permission objects.
    """
    return f"{permission_obj.content_type.app_label}.{permission_obj.codename}"


def permissions_to_strings(permission_objs: list[Permission] | models.QuerySet[Permission]) -> set[str]:
    """
    Returns a set of strings of the permissions in the list of permission objects.
    """
    return {permission_to_string(perm) for perm in permission_objs}


def string_to_permission(permission_str: str) -> Permission:
    """
    Returns the Permission object from the permission_str (auth.add_group -> <Permission: Auth | Group | Can add Group>)
    permission_str can be a string or a list of strings.
    """
    app_label, codename = permission_str.split(".", 1)
    return Permission.objects.get(content_type__app_label=app_label, codename=codename)


def strings_to_permissions(permission_strs: list[str]) -> set[Permission]:
    """
    Returns the set of Permission objects from the list of permission_strs.
    """
    return {string_to_permission(perm) for perm in permission_strs}


def get_app_model_action_from_permission(permission):
    if isinstance(permission, Permission):
        permission = permission_to_string(permission)

    parts = permission.split(".")
    app_label = parts[0]
    perm_action_model = parts[1]
    perm_action = perm_action_model.split("_")[0]
    model_name = "_".join(perm_action_model.split("_")[1:])
    return app_label, model_name, perm_action



def get_permission_for_model_action(model, action):
    """
    Resolve the named permission for a given model (or instance) and action (e.g. view or add).

    :param model: A model or instance
    :param action: View, add, change, or delete (string)
    """
    # Resolve to the "concrete" model (for proxy models)
    model = model._meta.concrete_model
    assert action in PERMISSION_ACTION, f"Action must be in {PERMISSION_ACTION}. Not {action}"
    return f"{model._meta.app_label}.{action}_{model._meta.model_name}"


# A few helper functions for common logic between User and AnonymousUser.
# def user_get_permissions(user, obj, from_name):
#     permissions = set()
#     name = "get_%s_permissions" % from_name
#     for backend in auth.get_backends():
#         if hasattr(backend, name):
#             func = getattr(backend, name)
#             permissions.update(func(user, obj))
#     return permissions


# def user_has_perm(user, perm, obj):
#     """
#     A backend can raise `PermissionDenied` to short-circuit permission checking.
#     """
#     for backend in auth.get_backends():
#         if not hasattr(backend, "has_perm"):
#             continue
#         try:
#             if backend.has_perm(user, perm, obj):
#                 return True
#         except PermissionDenied:
#             return False
#     return False


# def user_has_module_perms(user, app_label):
#     """
#     A backend can raise `PermissionDenied` to short-circuit permission checking.
#     """
#     for backend in auth.get_backends():
#         if not hasattr(backend, "has_module_perms"):
#             continue
#         try:
#             if backend.has_module_perms(user, app_label):
#                 return True
#         except PermissionDenied:
#             return False
#     return False


def is_owner(user, obj):
    """
    Is the given user owner of the object (created_user)
    """

    if hasattr(obj, "created_user"):
        username_field = getattr(user, settings.USERNAME_FIELD)
        if obj.created_user == username_field:
            return True

    return False


def user_has_model_perms(user, model: models.Model, action: str) -> bool:
    """
    Check if a user has permissions to [view, change, delete, add] an object.
    For add, obj must be the model.
    """
    if action not in PERMISSION_ACTION:
        raise ImproperlyConfigured(
            f"action must be in {PERMISSION_ACTION}. Not {action}"
        )
    req_perm = get_permission_for_model_action(model=model, action=action)
    return req_perm in permissions_to_strings(user.all_permissions)



def raise_permission_denied(user, model_obj, action):
    if action == "add":
        log.error(
            f"User '{user}' does not have the permission to {action} objects to model '{model_obj}'"
        )
        raise PermissionDenied(f"You do not have permission to {action} data.")
    else:
        log.error(
            f"User '{user}' does not have the permission to {action} object '{model_obj}'"
        )
        raise PermissionDenied(f"You do not have permission to {action} this data.")
