from django.utils import timezone

class ChangeLoggingSerializerMixin:
    """
    The serializer updates the fields created_user on create (POST) and last_updated_user on edit (PUT/PATCH).
    """
    
    class Meta:
        abstract = True
        read_only_fields = ('last_updated', 'last_updated_user', 'created', 'created_user')
    
    
    def get_current_user_email(self):
        request = self.context.get('request', None)     # type: ignore
        if request:
            return request.user.email


    def create(self, validated_data):
        validated_data['created_user'] = self.get_current_user_email()
        validated_data['created'] =timezone.now()
        return super().create(validated_data)       # type: ignore


    def update(self, instance, validated_data):
        instance.last_updated_user = self.get_current_user_email()
        instance.last_updated = timezone.now()
        return super().update(instance, validated_data)     # type: ignore