from ..functions.models import get_app_model_url
from ..functions.permissions import get_permission_for_model
from .button import menu_button_create


class MenuEntry:
    def __init__(
            self,
            model=None,
            title=None,
            url=None,
            request=None,
            permissions=[],
            is_header=False
        ):
        assert model is not None or title is not None, f"model or title and url must be set in {self.__class__}"
        if model:
            assert request, f"request must be set if model is set in {self.__class__}"
            all_user_permissions = request.user.get_all_permissions()
            view_perm = get_permission_for_model(model=model, action="view")
            add_perm = get_permission_for_model(model=model, action="add")
            self.title = model._meta.verbose_name_plural
            self.url = get_app_model_url(model) if view_perm in all_user_permissions else None
            if add_perm in all_user_permissions:
                self.button_add = menu_button_create(model)
        else:
            self.title = title
            self.url = url if url else None
        self.permissions = permissions
        self.is_header = is_header
    
    def __repr__(self):
        return f"{self.title} -> {self.url}"
    
    def __eq__(self, other):
        if isinstance(other, MenuEntry):
            return self.title == other.title \
                and self.url == other.url \
                and self.permissions == other.permissions \
                and self.is_header == other.is_header
        return False



