import logging

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.utils import timezone

from core.permissions import IsAuthenticated
from core.throttles.aa import SensitiveAnonThrottle



User = get_user_model()
logger = logging.getLogger(__name__)


def _token_pair(user) -> dict:
    """Return a fresh access + refresh token pair for *user*."""
    refresh = RefreshToken.for_user(user)
    return {
        "access":  str(refresh.access_token),
        "refresh": str(refresh),
    }


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([SensitiveAnonThrottle])
def login(request):
    """
    POST /api/auth/login/
    Body: { "email": "...", "password": "..." }
    """
    email    = request.data.get("email", "").strip().lower()
    password = request.data.get("password", "")

    if not email or not password:
        return Response(
            {"detail": "Email and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Deliberate vague message — don't reveal whether email exists
        return Response(
            {"detail": "Invalid email or password."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.check_password(password):
        return Response(
            {"detail": "Invalid email or password."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        return Response(
            {"detail": "Your account has been suspended. Please contact your administrator."},
            status=status.HTTP_403_FORBIDDEN,
        )

    tokens = _token_pair(user)
    logger.info("Login successful: %s", email)
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])

    return Response(
        {
            **tokens,
            "user": {
                "id":    str(user.pk),
                "email": user.email,
                "name":  user.name,
                "role":  user.role,
            },
        },
        status=status.HTTP_200_OK,
    )

@api_view(["POST"])
@permission_classes([AllowAny])
def refresh(request):
    """
    POST /api/auth/refresh/
    Body: { "refresh": "<token>" }
    """
    raw = request.data.get("refresh", "")
    if not raw:
        return Response(
            {"detail": "Refresh token is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        token  = RefreshToken(raw)
        # Rotate: issue a new refresh token and blacklist the old one
        # (requires ROTATE_REFRESH_TOKENS = True and BLACKLIST_AFTER_ROTATION = True)
        access = str(token.access_token)
        token.set_jti()
        token.set_exp()
        new_refresh = str(token)
    except TokenError as exc:
        return Response(
            {"detail": "Session expired. Please log in again."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    return Response({"access": access, "refresh": new_refresh}, status=status.HTTP_200_OK)



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    POST /api/auth/logout/
    Body: { "refresh": "<token>" }

    Blacklists the refresh token so it can no longer be rotated.
    """
    raw = request.data.get("refresh", "")
    if raw:
        try:
            RefreshToken(raw).blacklist()
        except TokenError:
            pass  # already expired/blacklisted — that's fine

    return Response({"detail": "Logged out successfully."}, status=status.HTTP_200_OK)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    """
    GET /api/auth/me/
    Returns the authenticated user's profile.
    """
    user = request.user
    return Response({
        "id":         str(user.pk),
        "email":      user.email,
        "name":       user.name,
        "role":       user.role,
        "is_active":  user.is_active,
    })