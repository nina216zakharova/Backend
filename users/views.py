import urllib.parse
from django.conf import settings
from django.http import JsonResponse, HttpResponseRedirect
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed, ValidationError

from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
    GoogleAuthSerializer,
)
from .services import (
    authenticate_google,
    get_google_auth_url,
)


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
    """
    Retrieve safe profile details for the currently authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


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


class GoogleAuthView(APIView):
    """
    Authenticate or register a user using Google credentials (id_token, access_token, or code).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user, token, is_new = authenticate_google(
                id_token=serializer.validated_data.get('id_token'),
                access_token=serializer.validated_data.get('access_token'),
                code=serializer.validated_data.get('code'),
                redirect_uri=serializer.validated_data.get('redirect_uri'),
            )
            return Response(
                {
                    "token": token.key,
                    "user": UserSerializer(user).data,
                    "is_new_user": is_new,
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
        except AuthenticationFailed as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response(
                {"detail": "Authentication failed. Please verify your Google credentials."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class GoogleLoginRedirectView(APIView):
    """
    Generate Google OAuth consent URL or redirect user to Google.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        state = request.GET.get('state')
        auth_url = get_google_auth_url(state=state)

        if request.GET.get('format') == 'json':
            return Response({"auth_url": auth_url}, status=status.HTTP_200_OK)

        return HttpResponseRedirect(auth_url)


class GoogleCallbackView(APIView):
    """
    Handle OAuth callback redirect from Google.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173').rstrip('/')
        error = request.GET.get('error')
        if error:
            redirect_target = f"{frontend_url}/login?error={urllib.parse.quote(error)}"
            return HttpResponseRedirect(redirect_target)

        code = request.GET.get('code')
        if not code:
            redirect_target = f"{frontend_url}/login?error={urllib.parse.quote('Authorization code was not provided')}"
            return HttpResponseRedirect(redirect_target)

        try:
            user, token, _ = authenticate_google(code=code)
            redirect_target = (
                f"{frontend_url}/login?token={token.key}"
                f"&email={urllib.parse.quote(user.email)}"
                f"&username={urllib.parse.quote(user.username)}"
            )
            return HttpResponseRedirect(redirect_target)
        except Exception as exc:
            redirect_target = f"{frontend_url}/login?error={urllib.parse.quote(str(exc))}"
            return HttpResponseRedirect(redirect_target)
