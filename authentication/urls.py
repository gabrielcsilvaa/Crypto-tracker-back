# authentication/urls.py
from django.urls import path
from .views import (
    RegisterView,
    LoginView,       # alias de TokenObtainPairView
    RefreshView,     # alias de TokenRefreshView
    MeView,
    MePasswordView,
    UserListView,
    UserDetailView,
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="token_obtain_pair"),
    path("refresh/", RefreshView.as_view(), name="token_refresh"),
    path("register/", RegisterView.as_view(), name="register"),
    path("me/", MeView.as_view(), name="me"),
    path("me/password/", MePasswordView.as_view(), name="me_password"),
    path("users/", UserListView.as_view(), name="users_list"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="users_detail"),
]
