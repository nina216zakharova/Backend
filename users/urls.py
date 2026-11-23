from django.urls import path
from . import views

urlpatterns = [
    path("", views.users_api, name="users-api"),
    path("register/", views.RegisterView.as_view(), name="user-register"),
    path("login/", views.LoginView.as_view(), name="user-login"),
    path("me/", views.CurrentUserView.as_view(), name="user-current"),
    path("logout/", views.LogoutView.as_view(), name="user-logout"),
    path("google/", views.GoogleAuthView.as_view(), name="user-google-auth"),
    path("google/login/", views.GoogleLoginRedirectView.as_view(), name="user-google-login-redirect"),
    path("google/callback/", views.GoogleCallbackView.as_view(), name="user-google-callback"),
    path("password-reset/", views.PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password-reset/validate/", views.PasswordResetValidateView.as_view(), name="password-reset-validate"),
    path("password-reset/confirm/", views.PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("password-change/", views.PasswordChangeView.as_view(), name="password-change"),
]
