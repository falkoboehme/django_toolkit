from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.signals import user_logged_in
from django.core.exceptions import FieldError, MultipleObjectsReturned, ObjectDoesNotExist, ImproperlyConfigured
from rest_framework import exceptions, serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.state import token_backend
from rest_framework_simplejwt.serializers import TokenRefreshSerializer, TokenObtainSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .mixins import ManyToManyWriteSerializerMixin, ChangeLoggingSerializerMixin
from ..functions.api_filters import dict_to_filter_params

import logging

log = logging.getLogger("fast_dev")


class APITokenRefreshSerializer(TokenRefreshSerializer):
    """
    Inherit from `TokenRefreshSerializer` and touch the database
    before re-issuing a new access token and ensure that the user
    exists and is active.
    """

    error_msg = 'Login failed'

    def validate(self, attrs):
        token_payload = token_backend.decode(attrs['refresh'])
        try:
            user = get_user_model().objects.get(pk=token_payload['user_id'])
        except get_user_model().DoesNotExist:
            log.error(f"User having id {token_payload['user_id']} does not exist")
            raise exceptions.AuthenticationFailed(
                self.error_msg, 'no_active_account'
            )

        #if not user.is_active or user.email != token_payload['user_email']:
        if not user.is_active:
            log.error(f"User {user} is not active")
            raise exceptions.AuthenticationFailed(
                self.error_msg, 'no_active_account'
            )

        log.debug(f"Token for {user} refreshed")
        return super().validate(attrs)



class APITokenAuthSerializer(TokenObtainSerializer):
    token_class = RefreshToken

    def validate(self, attrs):
        data = {}
        email = attrs[self.username_field]
        password = attrs["password"]
        request = self.context["request"]
        # pass the auth_module to authenticate, so it is passed to user_login_failed-Signal in credentials
        user = authenticate(request=request, username=email, password=password, auth_module='Token')

        if user is None:
            raise exceptions.AuthenticationFailed(
                'Login failed',
                "no_active_account",
            )
        else:
            user_logged_in.send(sender=user.__class__, request=request, user=user, auth_module='Token')
            refresh = self.get_token(user)
            data["refresh"] = str(refresh)
            data["access"] = str(refresh.access_token)
        return data



class BaseSerializer(serializers.HyperlinkedModelSerializer, serializers.ModelSerializer):
    """
    Basis Serializer
    adds fields id, url and display
    """
    serializer_related_field = serializers.HyperlinkedRelatedField
    id = serializers.IntegerField(read_only=True)
    display = serializers.SerializerMethodField(read_only=True)

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
    def to_internal_value(self, data):

        if data is None:
            return None
        
        # Dictionary of related object attributes
        if isinstance(data, dict):
            params = dict_to_filter_params(data)
            queryset = self.Meta.model.objects
            try:
                return queryset.get(**params)
            except ObjectDoesNotExist:
                raise ValidationError(f"Related object not found using the provided attributes: {params}")
            except MultipleObjectsReturned:
                raise ValidationError(f"Multiple objects match the provided attributes: {params}")
            except FieldError as e:
                raise ValidationError(e)

        # Integer PK of related object
        try:
            # Cast as integer in case a PK was mistakenly sent as a string
            pk = int(data)
        except (TypeError, ValueError):
            raise ValidationError(
                f"Related objects must be referenced by numeric ID or by dictionary of attributes. Received an "
                f"unrecognized value: {data}"
            )

        # Look up object by PK
        try:
            return self.Meta.model.objects.get(pk=pk)
        except ObjectDoesNotExist:
            raise ValidationError(f"Related object not found using the provided numeric ID: {pk}")