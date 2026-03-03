import logging
from django.db.models import fields


log = logging.getLogger(__name__)


class ManyToManyWriteSerializerMixin:
    
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
        ret = self.write_many_to_many(instance, validated_data)
        if ret is None:
            return super().update(instance, validated_data)      # type: ignore
        else:
            return ret
