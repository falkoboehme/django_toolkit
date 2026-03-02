from django.utils import timezone
from django.db.models import fields
from rest_framework.exceptions import ValidationError
from django.core.exceptions import FieldError, MultipleObjectsReturned, ObjectDoesNotExist
from ..functions.api_filters import dict_to_filter_params

import logging
log = logging.getLogger(__name__)



class ChangeLoggingSerializerMixin:
    """
    The serializer updates the fields created_user on create (POST) and last_updated_user on edit (PUT/PATCH).
    """
    
    class Meta:
        abstract = True
        read_only_fields = ('last_updated', 'last_updated_user', 'created', 'created_user')
    
    def get_current_user_email(self):
        request = self.context.get('request', None)
        if request:
            return request.user.email

    def create(self, validated_data):
        validated_data['created_user'] = self.get_current_user_email()
        validated_data['created'] =timezone.now()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        instance.last_updated_user = self.get_current_user_email()
        instance.last_updated = timezone.now()
        return super().update(instance, validated_data)



# class WritableNestedSerializerMixin:
#     """
#     Represents an object related through a ForeignKey field. On write, it accepts a primary key (PK) value or a
#     dictionary of attributes which can be used to uniquely identify the related object. This class should be
#     subclassed to return a full representation of the related object on read.
#     """

#     def to_internal_value(self, data):

#         if data is None:
#             return None
        
#         # Dictionary of related object attributes
#         if isinstance(data, dict):
#             params = dict_to_filter_params(data)
#             queryset = self.Meta.model.objects

#             try:
#                 return queryset.get(**params)
#             except ObjectDoesNotExist:
#                 raise ValidationError(f"Related object not found using the provided attributes: {params}")
#             except MultipleObjectsReturned:
#                 raise ValidationError(f"Multiple objects match the provided attributes: {params}")
#             except FieldError as e:
#                 raise ValidationError(e)

#         # Integer PK of related object
#         try:
#             # Cast as integer in case a PK was mistakenly sent as a string
#             pk = int(data)
#         except (TypeError, ValueError):
#             raise ValidationError(
#                 f"Related objects must be referenced by numeric ID or by dictionary of attributes. Received an "
#                 f"unrecognized value: {data}"
#             )

#         # Look up object by PK
#         try:
#             return self.Meta.model.objects.get(pk=pk)
#         except ObjectDoesNotExist:
#             raise ValidationError(f"Related object not found using the provided numeric ID: {pk}")



class ManyToManyWriteSerializerMixin:
    
    def write_many_to_many(self, instance, validated_data):
        # TODO: Translate
        # Wenn vorhanden, ManyToMany Beziehung auflösen
        # Da ein Model mehrere ManyToMany-Relationen haben kann, müssen wir erst alle einsammeln und
        # danach verarbeiten (damit bei POST das Model ohne jegliche ManyToMany-Relation angelegt werden kann)
        request = self.context["request"]
        model_class = self.Meta.model
        many_to_many_fieldnames = {}
        validated_data_without_many_to_many = {}
        for fieldname, obj in validated_data.items():
            # Ist es ein ManyToMany Feld des Models?
            if isinstance(obj, list) and hasattr(model_class, fieldname):
                model_field_class = getattr(model_class, fieldname)
                if isinstance(model_field_class, fields.related_descriptors.ManyToManyDescriptor):
                    many_to_many_fieldnames[fieldname] = obj
            else:
                validated_data_without_many_to_many[fieldname] = obj
        if len(many_to_many_fieldnames) > 0:
            log.debug(f"Validated-Data: {validated_data}")
            if request.method == "POST":
                # Modell ohne ManyToMany anlegen
                instance = model_class.objects.create(**validated_data_without_many_to_many)
                # Die gewünschten Relationen hinzufügen
                for fieldname in many_to_many_fieldnames:
                    field = getattr(instance, fieldname)
                    for item in many_to_many_fieldnames[fieldname]:
                        field.add(item)
                        log.debug(f"{model_class.__name__} '{instance}' [{fieldname}] adding {item}")
            elif request.method in ["PUT", "PATCH"]:
                # Modell ohne ManyToMany updaten
                instance = super().update(instance, validated_data_without_many_to_many)
                # Jetzt noch die ManyToMany Felder bearbeiten
                for fieldname in many_to_many_fieldnames:
                    field = getattr(instance, fieldname)
                    # Die gewünschten Relationen hinzufügen
                    for item in many_to_many_fieldnames[fieldname]:
                        field.add(item)
                        log.debug(f"{model_class.__name__} '{instance}' [{fieldname}] adding {item}")
                    # Nicht gewünschte Relationen entfernen
                    for item in field.all():
                        if item not in many_to_many_fieldnames[fieldname]:
                            field.remove(item)
                            log.debug(f"{model_class.__name__} '{instance}' [{fieldname}] removing {item}")
            return instance
        else:
            return None
    

    def create(self, validated_data):
        ret = self.write_many_to_many(None, validated_data)
        if ret is None:
            return super().create(validated_data)
        else:
            return ret


    def update(self, instance, validated_data):
        ret = self.write_many_to_many(instance, validated_data)
        if ret is None:
            return super().update(instance, validated_data)
        else:
            return ret
