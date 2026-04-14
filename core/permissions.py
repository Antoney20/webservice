# ---------------------------------------------------------------------------
# Permission logic web service
#
# PublicReadEditorWrite        GET: anyone | POST/PUT/PATCH: editor+ | DELETE: admin
# PublicReadAdminWrite         GET: anyone | all writes: admin
# PublicReadAuthCreate         GET: anyone | POST: authenticated | PUT/PATCH/DELETE: admin
# AuthenticatedReadAdminWrite  GET: authenticated | writes: admin
# IsAdmin                      everything: admin only
# AllowAnonymous               everything: public (used explicitly on views)
# ---------------------------------------------------------------------------

from rest_framework.permissions import BasePermission, SAFE_METHODS, AllowAny  # noqa: F401


def _is_authenticated(request) -> bool:
    return bool(request.user and request.user.is_authenticated and request.user.is_active)

def _is_editor(request) -> bool:
    return _is_authenticated(request) and request.user.is_editor_or_above

def _is_admin(request) -> bool:
    return _is_authenticated(request) and request.user.is_admin


class IsAuthenticatedActive(BasePermission):
    """Any valid, active user."""
    message = "Authentication required."

    def has_permission(self, request, view):
        return _is_authenticated(request)


class IsEditor(BasePermission):
    """Editor or admin role."""
    message = "Editor or admin role required."

    def has_permission(self, request, view):
        return _is_editor(request)


class IsAdmin(BasePermission):
    """Admin role only."""
    message = "Admin role required."

    def has_permission(self, request, view):
        return _is_admin(request)


class PublicReadEditorWrite(BasePermission):
    """
    GET / HEAD / OPTIONS  → public
    POST / PUT / PATCH    → editor or admin
    DELETE                → admin only
    """
    message = "Insufficient permissions."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if request.method == "DELETE":
            return _is_admin(request)
        return _is_editor(request)


class PublicReadAdminWrite(BasePermission):
    """
    GET / HEAD / OPTIONS           → public
    POST / PUT / PATCH / DELETE    → admin only
    """
    message = "Admin role required to modify this resource."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return _is_admin(request)


class PublicReadAuthCreate(BasePermission):
    """
    GET / HEAD / OPTIONS  → public
    POST                  → any active authenticated user
    PUT / PATCH / DELETE  → admin only
    """
    message = "Authentication required to perform this action."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if request.method == "POST":
            return _is_authenticated(request)
        return _is_admin(request)


class AuthenticatedReadAdminWrite(BasePermission):
    """
    GET / HEAD / OPTIONS           → authenticated active users only
    POST / PUT / PATCH / DELETE    → admin only
    """
    message = "Authentication required."

    def has_permission(self, request, view):
        if not _is_authenticated(request):
            return False
        if request.method not in SAFE_METHODS:
            return _is_admin(request)
        return True