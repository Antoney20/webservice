import logging
from django.http import JsonResponse

logger = logging.getLogger(__name__)

BLOCKED_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".sh", ".js", ".msi", ".dll", ".scr", ".ps1"
}

class UploadSecurityMiddleware:
    """
    Blocks suspicious file uploads.
    Does NOT ban IPs — only rejects request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in ("POST", "PUT", "PATCH") and request.FILES:
            for file in request.FILES.values():
                name = file.name.lower()

                for ext in BLOCKED_EXTENSIONS:
                    if name.endswith(ext):
                        logger.warning(
                            "Blocked suspicious upload: %s from %s",
                            name,
                            request.META.get("REMOTE_ADDR"),
                        )
                        return JsonResponse(
                            {
                                "success": False,
                                "detail": f"File type '{ext}' is not allowed."
                            },
                            status=400,
                        )

        return self.get_response(request)