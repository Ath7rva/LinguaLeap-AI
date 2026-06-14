import httpx

from app.core.config import get_settings

settings = get_settings()


def send_transactional_email(to: str, subject: str, html: str) -> bool:
    if settings.email_delivery_mode != "resend" or not settings.resend_api_key:
        return False
    try:
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={"from": settings.email_from, "to": [to], "subject": subject, "html": html},
            timeout=8,
        )
        response.raise_for_status()
        return True
    except httpx.HTTPError:
        return False
