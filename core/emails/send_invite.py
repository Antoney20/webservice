import logging
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


def send_invite_email(invitation, invite_link, invited_by=None):
    """Send the CEMA Web Service account invitation."""
    recipient  = invitation.email
    from_email = settings.EMAIL_HOST_USER
    subject    = "CEMA Web Service — Account Invitation"

    html_content = render_to_string("invite/invited.html", {
        "user_name":     recipient.split("@")[0],
        "invite_link":   invite_link,
        "role":          invitation.get_role_display(),
        "invited_by":    invited_by.name if invited_by else None,
        "expires_at":    invitation.invite_expires_at,
        "support_email": from_email,
        "current_year":  timezone.now().year,
    })

    try:
        email = EmailMultiAlternatives(subject=subject, body="", from_email=from_email, to=[recipient])
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        logger.info("Invite email sent to %s", recipient)
        return True
    except (SMTPException, Exception) as exc:
        logger.error("Failed to send invite email to %s: %s", recipient, exc, exc_info=True)
        return False