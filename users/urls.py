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

    # Partner explore & discovery endpoints
    path("explore/", views.PartnerExploreView.as_view(), name="user-explore"),
    path("discover/", views.PartnerExploreView.as_view(), name="user-discover"),

    # Self profile management endpoints
    path("profile/", views.MyProfileView.as_view(), name="user-profile-manage"),
    path("profile/completion/", views.ProfileCompletionView.as_view(), name="user-profile-completion"),

    # Public user & profile endpoints
    path("<int:pk>/", views.UserDetailView.as_view(), name="user-detail"),
    path("<int:pk>/profile/", views.PublicProfileDetailView.as_view(), name="user-public-profile"),
]
