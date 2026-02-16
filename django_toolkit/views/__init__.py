from .list import DTListView
from .detail import DTDetailView
from .create import DTCreateView
from .update import DTUpdateView
from .delete import DTDeleteView
from .login_logout import UserLoginView, UserLogoutView
from .home import HomeView


__all__ = [
    'DTDetailView',
    'DTListView',
    'DTCreateView',
    'DTUpdateView',
    'DTDeleteView',
    'UserLoginView',
    'UserLogoutView',
    'HomeView',
]
