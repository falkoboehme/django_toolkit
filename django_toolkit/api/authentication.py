import hashlib
import logging
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from ..functions.request import get_client_ip

log = logging.getLogger("toolkit")





def hash_token(raw_token):
    """Hash raw token using SHA256."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


def get_api_token_model():
    try:
        app_label, model_name = settings.DT_API_TOKEN_MODEL.split('.', 1)
    except ValueError as error:
        raise RuntimeError('DT_API_TOKEN_MODEL must be in the format "app_label.ModelName".') from error

    return apps.get_model(app_label, model_name)


class DTApiTokenAuthentication(BaseAuthentication):
    """
    Custom API Token Authentication.
    
    Expects request header:
        Authorization: Token <raw_token>
    
    Validates token against DTApiToken.token_hash.
    Optionally validates client IP against DTApiTokenAllowedCIDR.
    """
    
    keyword = 'Token'

    def authenticate_header(self, request):
        return self.keyword
    
    def authenticate(self, request):
        """
        Authenticate request using API token.
        Returns (user, token) or None (to pass to next auth backend).
        Raises AuthenticationFailed on validation errors.
        """
        auth = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth:
            return None  # Pass to next auth backend
        
        try:
            auth_type, raw_token = auth.split()
        except ValueError:
            raise AuthenticationFailed('Invalid Authorization header format.')
        
        if auth_type.lower() != self.keyword.lower():
            return None  # Not a token auth header, pass to next backend
        
        if not raw_token:
            raise AuthenticationFailed('Empty token.')
        
        # Hash raw token and lookup
        token_hash = hash_token(raw_token)
        token_model = get_api_token_model()
        
        try:
            token_obj = token_model.objects.select_related('user').get(token_hash=token_hash)
        except token_model.DoesNotExist:
            raise AuthenticationFailed('Invalid token.')

        if token_obj.valid_until is not None and token_obj.valid_until <= timezone.now():
            log.warning(f"Token {token_obj.name} ({token_obj.user}) rejected because it expired at {token_obj.valid_until}")  # type: ignore
            raise AuthenticationFailed('Token has expired.')
        
        # Check CIDR restrictions if defined
        if token_obj.allowed_cidrs.exists():    # type: ignore
            client_ip = get_client_ip(request)
            
            if not client_ip:
                log.warning(f'Token {token_obj.name} ({token_obj.user}) access denied because no client IP could be determined')
                raise AuthenticationFailed('IP address is not configured for this token.')
            
            try:
                # Check if client IP is in any allowed CIDR range
                allowed = token_obj.allowed_cidrs.filter(   # type: ignore
                    cidr__contains_ip=client_ip
                ).exists()
            except ValidationError as error:
                log.warning(f"Token {token_obj.name} ({token_obj.user}) CIDR validation failed for client IP {client_ip}: {error}") # type: ignore
                raise AuthenticationFailed(f'IP address {client_ip} is not configured for this token.') from error
            
            if not allowed:
                log.warning(f'Token {token_obj.id} access denied from IP {client_ip}')  # type: ignore
                raise AuthenticationFailed(f'IP address {client_ip} is not configured for this token.')
        
        return (token_obj.user, token_obj)
