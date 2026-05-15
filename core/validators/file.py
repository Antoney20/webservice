import os
import logging

from django.core.exceptions import ValidationError

from core.middleware.tracking import get_client_ip, record_throttle_violation


logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".ppt", ".pptx", ".csv", ".txt", 
    ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".mp4", ".mp3", 
}

BLOCKED_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".sh", ".ps1", ".msi",
    ".vbs", ".js", ".jar", ".com", ".scr", ".pif",
    ".reg", ".dll", ".sys", ".bin", ".iso",
}

MAX_FILE_SIZE = 60 * 1024 * 1024   #60mbs


def validate_file(file, request=None):
    """
    Validate uploaded file — extension, size, and blocked types.
    If request is provided, auto-bans IP on blocked extension attempts.
    """
    name      = file.name.lower()
    ext       = os.path.splitext(name)[1]
    file_size = file.size


    if ext in BLOCKED_EXTENSIONS:
        ip = get_client_ip(request) if request else "unknown"
        logger.warning("Blocked file upload attempt: ext=%s ip=%s file=%s", ext, ip, file.name)
        if request:
            record_throttle_violation(ip)
            for _ in range(10):
                record_throttle_violation(ip)
        raise ValidationError(
            f"File type '{ext}' is not allowed. Potentially dangerous file rejected."
        )

    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"File type '{ext}' is not supported. "
            f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Size check
    if file_size > MAX_FILE_SIZE:
        size_mb = file_size / (1024 * 1024)
        raise ValidationError(
            f"File size {size_mb:.1f} MB exceeds the 60 MB limit."
        )

    return file