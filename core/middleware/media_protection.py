"""
Middleware that guards all files served under MEDIA_URL.

"""

from __future__ import annotations

import logging
from pathlib import PurePosixPath
from urllib.parse import urlparse

from django.conf import settings
from django.http import HttpRequest, JsonResponse

import jwt

logger = logging.getLogger(__name__)


ALLOWED_EXTENSIONS: frozenset[str] = frozenset(
    {
        # Images
        ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".avif",
        # Documents
        ".pdf", ".doc", ".docx",
        ".xls", ".xlsx",
        ".ppt", ".pptx",
        ".csv", ".txt", 
    }
)

# Extensions that render inline in the browser
INLINE_EXTENSIONS: frozenset[str] = frozenset(
    {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".avif", ".pdf"}
)

# Methods that read a file — origin/referer check applies
READ_METHODS: frozenset[str] = frozenset({"GET", "HEAD", "OPTIONS"})

# Methods that mutate — JWT required
WRITE_METHODS: frozenset[str] = frozenset({"POST", "PUT", "PATCH", "DELETE"})



def _json(message: str, status: int) -> JsonResponse:
    return JsonResponse({"success": False, "detail": message}, status=status)


def _allowed_hosts() -> list[str]:
    """
    Build a normalised list of bare hostnames from MEDIA_ALLOWED_ORIGINS
    (or ALLOWED_HOSTS as fallback).  Wildcards and empty strings are skipped.
    """
    raw: list[str] = getattr(
        settings,
        "MEDIA_ALLOWED_ORIGINS",
        getattr(settings, "ALLOWED_HOSTS", []),
    )
    hosts: list[str] = []
    for entry in raw:
        if not entry or entry == "*":
            continue
        parsed = urlparse(entry if "://" in entry else f"https://{entry}")
        host = (parsed.hostname or "").lower()
        if host:
            hosts.append(host)
    return hosts


def _host_from_url(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def _is_same_site(request: HttpRequest) -> bool:
    """
    Return True when the request comes from an allowed origin.

    Detection order:
      1. Sec-Fetch-Site  — most reliable (set by all modern browsers)
      2. Origin header
      3. Referer header
      4. No header       → direct navigation → False
    """

    # ── 1. Sec-Fetch-Site ─────────────────────────────────────────────
    sec_fetch_site = request.META.get("HTTP_SEC_FETCH_SITE", "")
    if sec_fetch_site in ("same-origin", "same-site"):
        return True
    if sec_fetch_site == "none":
        # Browser explicitly signals: user navigated directly (new tab, bookmark)
        return False
    # "cross-site" or absent — fall through to origin/referer

    allowed = _allowed_hosts()
    if not allowed:
        logger.warning(
            "[media] MEDIA_ALLOWED_ORIGINS is empty — all origins permitted"
        )
        return True

    # ── 2. Origin header ──────────────────────────────────────────────
    origin = request.META.get("HTTP_ORIGIN", "")
    if origin:
        return _host_from_url(origin) in allowed

    # ── 3. Referer header ─────────────────────────────────────────────
    referer = request.META.get("HTTP_REFERER", "")
    if referer:
        return _host_from_url(referer) in allowed

    # ── 4. No navigation headers → assume direct access ───────────────
    return False


def _decode_token(token: str) -> dict | None:
    secret    = getattr(settings, "JWT_SECRET_KEY", settings.SECRET_KEY)
    algorithm = getattr(settings, "JWT_ALGORITHM",  "HS256")
    try:
        return jwt.decode(token, secret, algorithms=[algorithm])
    except jwt.ExpiredSignatureError:
        logger.debug("[media] JWT expired")
    except jwt.InvalidTokenError as exc:
        logger.debug("[media] JWT invalid: %s", exc)
    return None


def _extract_token(request: HttpRequest) -> str | None:
    # 1. Authorization: Bearer <token>
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    # 2. HttpOnly cookie
    cookie_name = getattr(settings, "JWT_COOKIE_NAME", "access_token")
    token = request.COOKIES.get(cookie_name)
    if token:
        return token
    # 3. ?token= query param  (for <img src> / <a href> with injected token)
    token = request.GET.get("token")
    if token:
        return token
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Middleware
# ─────────────────────────────────────────────────────────────────────────────

class MediaProtectionMiddleware:
    """
    Guards every path under MEDIA_URL.

    GET / HEAD  → public, but same-site requests only
    POST / etc. → requires a valid JWT
    Bad ext     → 415
    """

    def __init__(self, get_response):
        self.get_response  = get_response
        media_url: str     = getattr(settings, "MEDIA_URL", "/media/")
        self.media_prefix  = "/" + media_url.strip("/")


    def __call__(self, request: HttpRequest):
        path   = request.path_info
        method = request.method.upper()

        # Fast-path: not a media path
        if not path.startswith(self.media_prefix):
            return self.get_response(request)

        ext = PurePosixPath(path).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            logger.warning(
                "[media] Blocked extension '%s' — %s", ext or "(none)", path
            )
            return _json(
                f"File type '{ext or '(none)'}' is not permitted.",
                status=415,
            )

        if method in READ_METHODS:
            if not _is_same_site(request):
                logger.info(
                    "[media] Blocked off-site/direct read — "
                    "Sec-Fetch-Site=%s Origin=%s Referer=%s path=%s",
                    request.META.get("HTTP_SEC_FETCH_SITE", "-"),
                    request.META.get("HTTP_ORIGIN",         "-"),
                    request.META.get("HTTP_REFERER",        "-"),
                    path,
                )
                return _json(
                    "This file may only be accessed from the site.",
                    status=403,
                )

            response = self.get_response(request)
            self._set_read_headers(response, ext, path)
            logger.debug("[media] Read allowed — %s", path)
            return response

        if method in WRITE_METHODS:
            token = _extract_token(request)
            if not token:
                return _json("Authentication required.", status=401)

            payload = _decode_token(token)
            if payload is None:
                return _json("Invalid or expired token.", status=401)

            request.media_user = payload
            logger.debug(
                "[media] Write granted — user=%s path=%s",
                payload.get("user_id") or payload.get("sub"),
                path,
            )
            return self.get_response(request)


        return _json("Method not allowed.", status=405)


    @staticmethod
    def _set_read_headers(response, ext: str, path: str) -> None:
        """
        Attach security + content-disposition headers to every allowed read.

        Cache-Control: private, no-store
            Tells the browser (and any intermediate proxy) not to cache the
            file, so it can't be retrieved later without going through the
            middleware again.

        X-Content-Type-Options: nosniff
            Prevents the browser from MIME-sniffing the response away from
            the declared content type.

        Content-Disposition:
            inline      — images and PDFs render in-browser when opened
                          from within the site via <img> / <object> / fetch.
            attachment  — office files and archives are always downloaded,
                          never rendered.
        """
        response["Cache-Control"]          = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"

        filename = PurePosixPath(path).name

        if ext in INLINE_EXTENSIONS:
            response["Content-Disposition"] = "inline"
        else:
            response["Content-Disposition"] = f'attachment; filename="{filename}"'