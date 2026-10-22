"""SMTP transport; verification and reminders never expose tokens in application logs."""

import smtplib
from email.message import EmailMessage

from app.config import Settings


def send_mail(settings: Settings, recipient: str, subject: str, body: str) -> None:
    if not settings.smtp_host:
        raise OSError("SMTP is not configured")
    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        if settings.smtp_starttls:
            smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)
