from ..functions.models import get_app_model_url
from ..functions.permissions import get_permission_for_model_action, permissions_to_strings
from .button import menu_button_create


class MenuEntry:
    def __init__(
            self,
            model=None,
            title=None,
            url=None,
            request=None,
            permissions=[],
            is_header=False,
            view_permission=False,
            add_permission=False,
        ):
        assert model is not None or title is not None, f"model or title and url must be set in {self.__class__}"
        if model:
            assert request, f"request must be set if model is set in {self.__class__}"
            all_user_permissions = permissions_to_strings(request.user.all_permissions)
            view_permission = get_permission_for_model_action(model=model, action="view") in all_user_permissions
            add_permission = get_permission_for_model_action(model=model, action="add") in all_user_permissions
            title = model._meta.verbose_name_plural
            url = get_app_model_url(model) if view_permission else None
            if add_permission:
                self.button_add = menu_button_create(model)
        
        self.url = url
        self.title = title
        self.permissions = permissions
        self.is_header = is_header
        self.view_permission = view_permission
        self.add_permission = add_permission

    
    def __repr__(self):
        return f"{self.title} -> {self.url}"
    
    def __eq__(self, other):
        if isinstance(other, MenuEntry):
            return self.title == other.title \
                and self.url == other.url \
                and self.permissions == other.permissions \
                and self.is_header == other.is_header \
                and self.view_permission == other.view_permission \
                and self.add_permission == other.add_permission
        return False



