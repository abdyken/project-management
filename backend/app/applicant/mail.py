"""SMTP transport; verification and reminders never expose tokens in application logs."""

from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage

from app.config import Settings


def _message(settings: Settings, recipient: str, subject: str, body: str) -> EmailMessage:
    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    return message


class Mailer:
    """One SMTP connection for several messages, opened on the first send.

    STARTTLS verifies the server certificate and host name: without a context smtplib
    accepts any certificate, and the app password would go to whoever answers.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._smtp: smtplib.SMTP | None = None

    def send(self, recipient: str, subject: str, body: str) -> None:
        if not self.settings.smtp_host:
            raise OSError("SMTP is not configured")
        if self._smtp is None:
            smtp = smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=10)
            try:
                if self.settings.smtp_starttls:
                    smtp.starttls(context=ssl.create_default_context())
                if self.settings.smtp_username:
                    smtp.login(self.settings.smtp_username, self.settings.smtp_password)
            except BaseException:
                smtp.close()
                raise
            self._smtp = smtp
        self._smtp.send_message(_message(self.settings, recipient, subject, body))

    def close(self) -> None:
        if self._smtp is not None:
            try:
                self._smtp.quit()
            except (OSError, smtplib.SMTPException):
                self._smtp.close()
            self._smtp = None

    def __enter__(self) -> Mailer:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def send_mail(settings: Settings, recipient: str, subject: str, body: str) -> None:
    with Mailer(settings) as mailer:
        mailer.send(recipient, subject, body)


def describe_error(error: BaseException) -> str:
    """For logs: the error class and SMTP code, never the recipient or the message."""
    code = getattr(error, "smtp_code", None)
    return f"{type(error).__name__}" + (f" (SMTP {code})" if code else "")


def stops_batch(error: BaseException) -> bool:
    """True when later messages in the same run would fail too (login, quota, connection).

    A refused recipient only affects that message.
    """
    return not isinstance(error, smtplib.SMTPRecipientsRefused)
