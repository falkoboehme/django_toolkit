from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.contrib.auth import logout as auth_logout
from ..forms import UserAuthenticationForm


class UserLoginView(LoginView):
    template_name = "django_toolkit/login.html"
    authentication_form = UserAuthenticationForm
    redirect_authenticated_user = True
    success_url = reverse_lazy("home")  # Replace 'home' with your home view name


class UserLogoutView(LogoutView):
    success_url = reverse_lazy("login")  # Redirect to the login page after logout
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        auth_logout(request)
        return HttpResponseRedirect(self.success_url)
