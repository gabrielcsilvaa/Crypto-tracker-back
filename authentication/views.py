# authentication/views.py
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, response, status
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import (
    UserSerializer,
    MeSerializer,              # compat
    UserCreateSerializer,
    UserUpdateSerializer,
    PasswordChangeSerializer,
)

User = get_user_model()

# Aliases para compatibilidade com imports existentes no seu urls.py
LoginView = TokenObtainPairView
RefreshView = TokenRefreshView

class RegisterView(generics.CreateAPIView):
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]

class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return response.Response(MeSerializer(request.user).data)

    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)

class MePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def patch(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response({"detail": "Senha alterada com sucesso."}, status=status.HTTP_200_OK)

class UserListView(generics.ListCreateAPIView):
    queryset = User.objects.all().order_by("-date_joined")
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return UserCreateSerializer
        return UserSerializer

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return UserUpdateSerializer
        return UserSerializer
