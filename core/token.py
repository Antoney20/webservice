import hmac
import os

from django.conf import settings
from django.http import JsonResponse


def _get_client_registry() -> dict[str, str]:
    return {
        "https://cema-africa.uonbi.ac.ke": os.getenv("CLIENT_TOKEN_WEB_CEMA", ""),
        "http://cema-africa.uonbi.ac.ke":  os.getenv("CLIENT_TOKEN_WEB_CEMA", ""),
        "https://raci.cema.africa":        os.getenv("CLIENT_TOKEN_RACI_CEMA", ""),
        "http://localhost:3000":           os.getenv("CLIENT_TOKEN_LOCALHOST", ""),
    }


def _safe_compare(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode(), b.encode())


class ClientTokenMiddleware:
    HEADER = "HTTP_X_CLIENT_TOKEN"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._is_exempt(request):
            return self.get_response(request)

        origin = request.META.get("HTTP_ORIGIN", "").rstrip("/")

        if not origin:
            return self.get_response(request)   # server-to-server, let through

        registry = _get_client_registry()

        if origin not in registry:
            return self._reject(f"Origin not permitted: {origin}")

        expected = registry[origin]
        if not expected:
            return self._reject("Client token not configured for this origin.")

        provided = request.META.get(self.HEADER, "")
        if not provided:
            return self._reject("Missing X-Client-Token header.")

        if not _safe_compare(provided, expected):
            return self._reject("Invalid X-Client-Token.")

        return self.get_response(request)

    def _is_exempt(self, request) -> bool:
        exempt = getattr(settings, "RACI_EXEMPT_PATHS", [])
        return any(request.path.startswith(p) for p in exempt)

    def _reject(self, detail: str):
        return JsonResponse({"detail": detail}, status=403)