from django.apps import apps
from django.db import models
from .permissions import ALL_OPERATIONS, PERMISSIION_ACTION


def get_app_label(model):
    """returns the app_label of a model"""
    return model._meta.app_label


def get_model_lower_name(model):
    """returns the model_name of a model in small letters"""
    return model._meta.model_name


def get_model_class_name(model):
    """returns the name of a model class as defined in the code"""
    return model.__name__


def get_model_url(model):
    return f"{model._meta.model_name}s"


def get_app_modelname_id(obj):
    """returns the app_label, model_name and id of an object"""
    if hasattr(obj._meta, "model"):
        # Object
        app_label = get_app_label(obj._meta.model)
        model_name = get_model_lower_name(obj._meta.model)
        object_id = obj.id
    else:
        # Model
        app_label = get_app_label(obj)
        model_name = get_model_lower_name(obj)
        object_id = None
    return (app_label, model_name, object_id)


def get_app_model_url(model, slash_start=True, slash_end=True):
    url = "/" if slash_start else ""
    url += f"{model._meta.app_label}/{get_model_url(model)}"
    url += "/" if slash_end else ""
    return url


def get_object_identifier(obj):
    """returns the unique object_identifier for an object (for the GUI)"""
    app_label, model_name, object_id = get_app_modelname_id(obj)
    return f"{app_label}.{model_name}:{object_id}"


def get_reverse(obj):
    app_label, model_name, object_id = get_app_modelname_id(obj)
    return f"{app_label}:{model_name}"


def get_model_pk(model):
    if model._meta.unique_together:
        return model._meta.unique_together[0]
    else:
        for field in model._meta.get_fields():
            if field.name != "id" and hasattr(field, "unique") and field.unique:
                return field.name


def get_obj_url(obj):
    """return the URL ob an object using PK (get_absolute_url must be defined in the model)"""
    model = obj._meta.model
    return model.get_absolute_url(obj)


def generate_link_to_obj(obj, user=None):
    obj_str = str(obj)
    if user:
        required_permission = get_model_permission_name(obj._meta.model, "view")    # type: ignore
        if hasattr(obj._meta.model, "get_absolute_url") and user.has_perm(required_permission, obj):
            return f'<a href="{get_obj_url(obj)}">{obj_str}</a>'
        else:
            return obj_str
    else:
        if hasattr(obj._meta.model, "get_absolute_url"):
            return f'<a href="{get_obj_url(obj)}">{obj_str}</a>'
        else:
            return obj_str


def get_user_defined_models():
    """returns all models, which are created by user defines apps"""
    return [
        model
        for model in apps.get_models()
        if model._meta.app_label not in ["admin", "auth", "contenttypes", "sessions"]
    ]


def get_user_defined_models_of_app(app_name):
    """returns all models of a app, which are created by user defines apps"""
    return [
        model
        for model in get_user_defined_models()
        if model._meta.app_label == app_name
    ]


def get_user_apps_with_models():
    """returns all app_labels, which are created by user"""
    user_apps_with_models = []
    for model in get_user_defined_models():
        app_label = model._meta.app_label
        if app_label not in user_apps_with_models:
            user_apps_with_models.append((app_label))
    return user_apps_with_models


def get_fields_of_model(model, selector="all"):
    """returns all fields, which are defined in the cards attribute of the model Meta class. Can be filted using the selector"""
    fields = []
    if hasattr(model._meta, "cards"):
        for card_col in model._meta.cards:
            for card in card_col:
                if selector == "all":
                    fields.extend(card.fields)
                elif selector == "ro":
                    for field in card.fields:
                        if field in card.ro_fields:
                            fields.append(field)
                elif selector == "rw":
                    for field in card.fields:
                        if field not in card.ro_fields:
                            fields.append(field)
                else:
                    raise Exception(
                        f"Selector '{selector}' unknown in get_fields_of_model"
                    )
    return fields


def get_foreignkey_fields_of_model(model):
    """returns all foreign key relations of a model (depending from an other model)"""
    related_fields = []
    for field in model._meta.fields:
        if hasattr(field, "resolve_related_fields"):
            related_fields.append(field)
    return related_fields


def get_related_name_from_field(field):
    if hasattr(field, "related_model"):
        through_model = field.remote_field.through
        for key, value in field.related_model._meta.fields_map.items():
            if value.related_model == through_model:
                return key


def get_model_operation_name(model: models.Model, operation: str) -> str:
    """Create a URL name based on model name and operation (e.g. 'user.list' or 'user.create')"""
    assert operation in ALL_OPERATIONS, f"Invalid operation '{operation}'. Must be one of {ALL_OPERATIONS}"
    return f"{model._meta.model_name.lower()}.{operation}"  # type: ignore


def get_model_permission_name(model: models.Model, perm: str) -> str:
    """Create a permission name based on model name and operation (e.g. 'user.view' or 'user.add')"""
    assert perm in PERMISSIION_ACTION, f"Invalid permission '{perm}'. Must be one of {PERMISSIION_ACTION}"
    return f"{model._meta.model_name.lower()}.{perm}"   # type: ignore


def get_model_operation_url(model: models.Model, operation: str) -> str:
    """Create a URL based on model name and operation (e.g. '/user/' or '/user/<id>/' or '/user/add/')"""
    assert operation in ALL_OPERATIONS, f"Invalid operation '{operation}'. Must be one of {ALL_OPERATIONS}"
    return f"/{model._meta.app_label}/{get_model_url(model)}/{operation}/"


