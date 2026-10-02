from django.urls import path
from core.views import login, refresh, logout, me


urlpatterns = [
    path("login/",   login,   name="auth-login"),
    path("refresh/", refresh, name="auth-refresh"),
    path("logout/",  logout,  name="auth-logout"),
    path("me/",      me,      name="auth-me"),
]

