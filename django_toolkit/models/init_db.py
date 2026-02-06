import copy
import shutil

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.exceptions import MultipleObjectsReturned
from django.db.models.fields import *
from django.db.models.fields.related import *
from django.db.models.fields.related_descriptors import *
from django.db.utils import IntegrityError
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from pathlib import Path

from ..functions.models import get_user_apps_with_models

class UniqueFieldNotDefined(Exception):
    pass

class FieldNotSet(Exception):
    pass

class InitDB:
    """
    Initialise database values for models.

    data:
    {
        <Model1>: [
            {field1: value1, field2: value2},
            {field1: value1, field2: value2},
        ],
        <Model2>: [
            {field3: value3, field4: [value4a, value4b]},
        ],
        Group: [
            {"name": "Default", "permissions": [{
                    User: ["view", "change"],
                }]
            },
    }
    """

    def __init__(self, class_name, data: dict) -> None:
        self.class_name = class_name
        self.data = data
        self.user_model = get_user_model()


    def init(self):
        for model, obj_list in self.data.items():
            for obj in obj_list:
                model_data = self.get_model_data(model, obj)
                if model == self.user_model:
                    self.create_user(model_data)
                else:
                    self.obj_writer(model, model_data)


    def get_model_data(self, model, obj):
        self.check_required_fields_are_set(model, obj)
        resolved_obj = copy.deepcopy(obj)
        for field_name in obj:
            field = model._meta.get_field(field_name)
            resolved_obj[field.name] = self.resolve_field(field, obj[field.name])
        # print(f"Resolved object: {resolved_obj}")
        return resolved_obj
    

    def obj_writer(self, model, model_data):
        new_model_data, m2m_fields = self.extract_m2m_fields(model, model_data)
        # Create new model, but do not save it yet
        model_instance = model()
        for field_name, value in new_model_data.items():
            setattr(model_instance, field_name, value)
        try:
            model_instance.save()
            self.add_m2m_fields(model_instance, m2m_fields)
            # print(f"object saved: {model}: {model_data}")
        except Exception as error:
            self.do_error_handling(error, model_data)
    

    def extract_m2m_fields(self, model, model_data):
        # remove the m2m_fields from the object, because they have to be saved after object creation
        new_model_data = copy.deepcopy(model_data)
        m2m_fields = {}
        for field_name, value in model_data.items():
            attr = getattr(model, field_name)
            if isinstance(attr, ManyToManyDescriptor):
                m2m_fields[field_name] = value
                new_model_data.pop(field_name)
        return (new_model_data, m2m_fields)


    def add_m2m_fields(self, instance, m2m_fields):
        for field_name, value_list in m2m_fields.items():
            field_attr = getattr(instance, field_name)
            for value in value_list:
                field_attr.add(value)
        instance.save()


    def resolve_field(self, field, field_value):
        #print(f"{field} = {field_value}")
        if field.is_relation:
            if field.related_model == Permission:
                return self.get_permission_ids(field, field_value)
            else:
                if isinstance(field, ManyToManyField):
                    return [self.get_related_instance(field, obj) for obj in field_value]
                elif isinstance(field, ForeignKey):
                    return self.get_related_instance(field, field_value)
        else:
            return field_value
            

    def check_required_fields_are_set(self, model, obj):
        for field in model._meta.fields:
            # print(field)
            if not field.blank and field.default == NOT_PROVIDED:
                self.check_field_is_set(model, field.name, obj)


    def check_field_is_set(self, model, field_name, obj):
        if field_name not in obj:
            raise FieldNotSet(f"Model '{model.__name__}': Field '{field_name}' missing in {obj}")


    def get_permission_ids(self, field, permission_list):
        #print(f"{field}: {permission_list}")
        ids = []
        for model_rights in permission_list:
            for perm_model, right_list in model_rights.items():
                content_type = self.get_content_type(perm_model)
                for right in right_list:
                    permission = Permission.objects.get(
                        content_type_id=content_type.id,
                        codename__startswith=right
                    )
                    ids.append(permission.id)   # type: ignore
        return ids
    

    def get_content_type(self, model):
        return ContentType.objects.get(app_label=model._meta.app_label, model=model._meta.model_name)


    def get_related_instance(self, field, field_value):
        related_model = field.related_model
        related_instance = None
        unique_fields = self.get_model_unique_fields(related_model)
        for unique in unique_fields:
            if isinstance(unique, str):
                # single unique field
                # print(f"single unique: searching {related_model}: {field_value}")
                field = related_model._meta.get_field(unique)
                related_field_value = self.resolve_field(field, field_value)
                get_filter = {field.name: related_field_value}
                related_instance = self.execute_query(related_model, get_filter)
                if related_instance:
                    # print(f"* Found Related Instance: {related_instance}")
                    return related_instance
                else:
                    get_filter.pop(field.name)
            else:
                # multiple fields together as unique
                # print(f"multiple unique: searching {related_model}: {field_value}")
                get_filter = {}
                # print(f"  need: {unique}, got: {field_value}")
                for single_unique_field in unique:
                    field = related_model._meta.get_field(single_unique_field)
                    if isinstance(field_value, str):
                        # print(f"  checking: {single_unique_field}")
                        resolved = self.resolve_field(field, field_value)
                        get_filter[single_unique_field] = resolved
                        related_instance = self.execute_query(related_model, get_filter)
                        if related_instance:
                            # print(f"* Found Related Instance: {related_instance}")
                            return related_instance
                        else:
                            get_filter.pop(single_unique_field)

                    elif isinstance(field_value, dict):
                        value = field_value[single_unique_field]
                        # print(f"  checking: {value}")
                        resolved = self.resolve_field(field, value)
                        get_filter[single_unique_field] = resolved
                        related_instance = self.execute_query(related_model, get_filter)
                        if related_instance:
                            # print(f"* Found Related Instance: {related_instance}")
                            return related_instance
                    elif isinstance(field_value, int):
                        return self.execute_query(related_model, {"pk": field_value})
                    else:
                        raise Exception("Not supported")
                related_instance = self.execute_query(related_model, get_filter)
                if related_instance:
                    # print(f"* Found Related Instance: {related_instance}")
                    return related_instance
    

    def execute_query(self, model, get_filter):
        # print(f"{model}: Get-Filter {get_filter}")
        try:
            return model.objects.get(**get_filter)
        except model.DoesNotExist:
            pass
        except Exception as error:
            print(f"execute_query: {error}")
            


    def get_model_unique_fields(self, model):
        model_pks = []
        for field in model._meta.get_fields():
            if field.name != "id" and hasattr(field, "unique") and field.unique:
                model_pks.append(field.name)
        if model._meta.unique_together:
            for tupel in model._meta.unique_together:
                model_pks.append(tupel)
        return model_pks


    def do_error_handling(self, error, obj):
        if type(error) == IntegrityError:
            if "UNIQUE constraint" in str(error):
                # we already have this object, do nothing
                pass
            else:
                print(f"Object: {obj} -> Error: {error}")
        else:
            print(error)


    def create_user(self, obj):
        new_obj, m2m_fields = self.extract_m2m_fields(self.user_model, obj)
        try:
            if 'is_superuser' in new_obj and new_obj['is_superuser']:
                new_user = self.user_model.objects.create_superuser(**new_obj)
            else:
                new_user = self.user_model.objects.create_user(**new_obj)
            new_user.save()
            self.add_m2m_fields(new_user, m2m_fields)
        except Exception as error:
            self.do_error_handling(error, obj)


    def cleanup(self, with_migrate=True):
        # clean up the database and migrations
        user_app_labels = get_user_apps_with_models()
        
        db_engine = settings.DATABASES['default']['ENGINE']
        if db_engine == 'django.db.backends.sqlite3':
            db_file = Path.joinpath(settings.BASE_DIR, 'db.sqlite3')
            Path.unlink(db_file, missing_ok=True)
        
        for app_label in user_app_labels:
            migration_dir = Path.joinpath(settings.BASE_DIR, app_label, 'migrations')
            try:
                shutil.rmtree(migration_dir)
            except FileNotFoundError:
                pass
        
        if with_migrate:
            call_command('makemigrations', *user_app_labels)
            call_command('migrate')

