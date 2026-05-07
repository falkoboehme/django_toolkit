from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.signals import user_logged_in
from django.core.exceptions import FieldError, MultipleObjectsReturned, ObjectDoesNotExist, ImproperlyConfigured
from rest_framework import exceptions, serializers
from rest_framework.exceptions import ValidationError
from .mixins import ManyToManyWriteSerializerMixin, ChangeLoggingSerializerMixin
from ..functions.api_filters import dict_to_filter_params



class BaseSerializer(serializers.HyperlinkedModelSerializer, serializers.ModelSerializer):
    """
    Base serializer.
    Adds fields id, url and display.
    """
    serializer_related_field = serializers.HyperlinkedRelatedField
    display = serializers.SerializerMethodField(read_only=True)

    def get_fields(self):
        fields = super().get_fields()

        model = getattr(getattr(self, 'Meta', None), 'model', None)
        if model is None:
            return fields

        pk_field = model._meta.pk
        pk_internal_type = pk_field.get_internal_type()

        if pk_internal_type == 'UUIDField':
            fields['id'] = serializers.UUIDField(read_only=True)
        elif pk_internal_type in {
            'AutoField',
            'BigAutoField',
            'SmallAutoField',
            'IntegerField',
            'BigIntegerField',
            'SmallIntegerField',
            'PositiveIntegerField',
            'PositiveBigIntegerField',
            'PositiveSmallIntegerField',
        }:
            fields['id'] = serializers.IntegerField(read_only=True)
        else:
            fields['id'] = serializers.CharField(read_only=True)

        return fields

    def get_display(self, obj):
        return str(obj)



class DTAPISerializer(ManyToManyWriteSerializerMixin, ChangeLoggingSerializerMixin, BaseSerializer):
    """
    Default serializer, supports:
    - write operations for many-to-many relations
    - change_logging updates
    """



class DTAPINestedSerializer(BaseSerializer):
    """
    Represents an object related through a ForeignKey field. On write, it accepts a primary key (PK) value or a
    dictionary of attributes which can be used to uniquely identify the related object. This class should be
    subclassed to return a full representation of the related object on read.
    """

    def _resolve_by_string(self, model, value: str):
        # 1) Try PK lookup first
        try:
            return model.objects.get(pk=value)
        except ObjectDoesNotExist:
            pass
        except (ValueError, TypeError):
            pass
        except MultipleObjectsReturned:
            raise ValidationError(f"Multiple objects match the provided string ID: {value}")

        # 2) Unique fields
        unique_fields = [
            f for f in model._meta.get_fields()
            if hasattr(f, "unique") and f.unique and not getattr(f, "primary_key", False)
        ]
        for field in unique_fields:
            try:
                return model.objects.get(**{field.name: value})
            except ObjectDoesNotExist:
                continue
            except (MultipleObjectsReturned, ValueError, TypeError):
                continue

        raise ValidationError(f"Related object not found using the provided value: '{value}'")

    def _resolve_model_instance(self, model, value):
        if value is None:
            return None

        if isinstance(value, int):
            try:
                return model.objects.get(pk=value)
            except ObjectDoesNotExist:
                raise ValidationError(f"Related object not found using the provided numeric ID: {value}")

        if isinstance(value, str):
            return self._resolve_by_string(model, value)

        if isinstance(value, dict):
            params = {}
            for key, val in value.items():
                try:
                    field = model._meta.get_field(key)
                except Exception:
                    params[key] = val
                    continue

                is_fk = getattr(field, "is_relation", False) and (
                    getattr(field, "many_to_one", False) or getattr(field, "one_to_one", False)
                )
                if is_fk:
                    related_model = field.related_model
                    params[key] = self._resolve_model_instance(related_model, val)
                else:
                    params[key] = val

            try:
                return model.objects.get(**params)
            except ObjectDoesNotExist:
                raise ValidationError(f"Related object not found using the provided attributes: {params}")
            except MultipleObjectsReturned:
                raise ValidationError(f"Multiple objects match the provided attributes: {params}")
            except (FieldError, ValueError, TypeError) as e:
                raise ValidationError(str(e))

        raise ValidationError(
            f"Related objects must be referenced by numeric ID, string unique identifier, or by dictionary of attributes. Received an "
            f"unrecognized value: {value}"
        )

    def to_internal_value(self, data):
        return self._resolve_model_instance(self.Meta.model, data)
        