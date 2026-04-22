# ---------------------------------------------------------------------------
# Permission classes
#
# AllowAll          everything: public
# AnonPostOnly      POST: anyone         | GET/PUT/PATCH/DELETE: admin
# PublicReadOnly    GET: public          | all writes: admin
# EditorWrite       GET: public          | POST/PUT/PATCH: editor+ | DELETE: admin
# AuthRead          GET: authenticated   | all writes: admin
# RequiresAuth      all methods: authenticated
# RequiresEditor    all methods: editor+
# RequiresAdmin     all methods: admin
# ---------------------------------------------------------------------------

from rest_framework.permissions import BasePermission, SAFE_METHODS


def _is_authenticated(request) -> bool:
    return bool(request.user and request.user.is_authenticated and request.user.is_active)

def _is_editor(request) -> bool:
    return _is_authenticated(request) and request.user.is_editor_or_above

def _is_admin(request) -> bool:
    return _is_authenticated(request) and request.user.is_admin


class AllowAll(BasePermission):
    """No restrictions."""

    def has_permission(self, request, view):
        return True


class AnonPostOnly(BasePermission):
    """POST: anyone. Everything else: admin."""
    message = "Insufficient permissions."

    def has_permission(self, request, view):
        if request.method == "POST":
            return True
        return _is_admin(request)


class PublicReadOnly(BasePermission):
    """GET: public. Writes: admin."""
    message = "Insufficient permissions."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return _is_admin(request)


class EditorWrite(BasePermission):
    """GET: public. POST/PUT/PATCH: editor+. DELETE: admin."""
    message = "Insufficient permissions."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if request.method == "DELETE":
            return _is_admin(request)
        return _is_editor(request)


class AuthRead(BasePermission):
    """GET: authenticated. Writes: admin."""
    message = "Insufficient permissions."

    def has_permission(self, request, view):
        if not _is_authenticated(request):
            return False
        if request.method not in SAFE_METHODS:
            return _is_admin(request)
        return True


class IsAuthenticated(BasePermission):
    """All methods: authenticated."""
    message = "Authentication required."

    def has_permission(self, request, view):
        return _is_authenticated(request)


class RequiresEditor(BasePermission):
    """All methods: editor+."""
    message = "Editor role required."

    def has_permission(self, request, view):
        return _is_editor(request)


class RequiresAdmin(BasePermission):
    """All methods: admin."""
    message = "Admin role required."

    def has_permission(self, request, view):
        return _is_admin(request)