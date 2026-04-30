import logging
from django.db import models
from django.db.models import fields


log = logging.getLogger(__name__)


class ManyToManyWriteSerializerMixin:

    def _deep_merge_dict(self, base, patch):
        merged = dict(base)
        for key, value in patch.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._deep_merge_dict(merged[key], value)
            else:
                merged[key] = value
        return merged

    def _merge_patch_json_fields(self, instance, validated_data):
        request = self.context.get("request")    # type: ignore
        if request is None or request.method != "PATCH":
            return validated_data

        model_class = self.Meta.model    # type: ignore
        merged_data = dict(validated_data)

        for field in model_class._meta.get_fields():
            if not isinstance(field, models.JSONField):
                continue

            field_name = field.name
            if field_name not in merged_data:
                continue

            incoming_value = merged_data[field_name]
            current_value = getattr(instance, field_name, None)

            if isinstance(current_value, dict) and isinstance(incoming_value, dict):
                merged_data[field_name] = self._deep_merge_dict(current_value, incoming_value)

        return merged_data
    
    def write_many_to_many(self, instance, validated_data):
        # TODO: Translate
        # Wenn vorhanden, ManyToMany Beziehung auflösen
        # Da ein Model mehrere ManyToMany-Relationen haben kann, müssen wir erst alle einsammeln und
        # danach verarbeiten (damit bei POST das Model ohne jegliche ManyToMany-Relation angelegt werden kann)
        request = self.context["request"]   # type: ignore
        model_class = self.Meta.model       # type: ignore
        many_to_many_fieldnames = {}
        validated_data_without_many_to_many = {}
        for fieldname, obj in validated_data.items():
            # Ist es ein ManyToMany Feld des Models?
            if isinstance(obj, list) and hasattr(model_class, fieldname):
                model_field_class = getattr(model_class, fieldname)
                if isinstance(model_field_class, fields.related_descriptors.ManyToManyDescriptor):      # type: ignore
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
                instance = super().update(instance, validated_data_without_many_to_many)        # type: ignore
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
            return super().create(validated_data)       # type: ignore
        else:
            return ret


    def update(self, instance, validated_data):
        validated_data = self._merge_patch_json_fields(instance, validated_data)
        ret = self.write_many_to_many(instance, validated_data)
        if ret is None:
            return super().update(instance, validated_data)      # type: ignore
        else:
            return ret
