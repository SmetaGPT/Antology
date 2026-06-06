from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage
import smtplib

from .config import Settings


@dataclass(frozen=True)
class EmailPayload:
    recipient_email: str
    subject: str
    body: str


class SmtpEmailSender:
    def __init__(self, settings: Settings):
        self._settings = settings

    def send(self, payload: EmailPayload) -> None:
        message = EmailMessage()
        message["From"] = self._settings.smtp_from_email
        message["To"] = payload.recipient_email
        message["Subject"] = payload.subject
        message.set_content(payload.body)

        with smtplib.SMTP(self._settings.smtp_host, self._settings.smtp_port, timeout=30) as server:
            if self._settings.smtp_use_tls:
                server.starttls()

            if self._settings.smtp_username:
                server.login(self._settings.smtp_username, self._settings.smtp_password)

            server.send_message(message)
