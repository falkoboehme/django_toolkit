from django.conf import settings
from django.contrib.auth.mixins import AccessMixin

class UserLoginRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if settings.LOGIN_REQUIRED:
            if not request.user.is_authenticated:
                return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)