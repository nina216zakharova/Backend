from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
)
from .models import Profile
from .serializers import ProfileSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

def users_api(request):
    """
    Baseline test endpoint created by team.
    Preserved for backward compatibility with existing tests.
    """
    if request.method != "GET":
        return JsonResponse(
            {
                "message": "Method not allowed",
                "status": "error",
            },
            status=405,
        )

    return JsonResponse({
        "message": "API is working!",
        "status": "success",
    })


class RegisterView(APIView):
    """
    Register a new user with email and password.
    Returns authentication token and safe user details upon success.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response(
                {
                    "token": token.key,
                    "user": UserSerializer(user).data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    Authenticate user by email and password.
    Returns authentication token upon success without revealing account existence on failure.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, _ = Token.objects.get_or_create(user=user)
            return Response(
                {
                    "token": token.key,
                    "user": UserSerializer(user).data,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CurrentUserView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, created = Profile.objects.get_or_create(
            user=request.user
        )

        profile_data = ProfileSerializer(profile).data

        return Response({
            "id": request.user.id,
            "email": request.user.email,
            "username": request.user.username,
            "profile": profile_data
        }, status=status.HTTP_200_OK)

    def patch(self, request):
        profile, created = Profile.objects.get_or_create(
            user=request.user
        )

        serializer = ProfileSerializer(
            profile,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    
class LogoutView(APIView):
    """
    Invalidate the active authentication token for the current user.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if hasattr(request, 'auth') and isinstance(request.auth, Token):
            request.auth.delete()
        elif hasattr(request.user, 'auth_token'):
            request.user.auth_token.delete()

        return Response(
            {"message": "Successfully logged out."},
            status=status.HTTP_200_OK,
        )
