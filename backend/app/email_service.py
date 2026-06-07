from __future__ import annotations

from dataclasses import asdict, dataclass
from email import policy
from email.header import decode_header, make_header
from email.message import EmailMessage
from email.parser import BytesParser
import email.utils
import imaplib
from pathlib import Path
import smtplib

from .config import Settings
from .repository import get_system_setting, set_system_setting

MAIL_PROVIDER_SETTING_KEY = "mail_provider_key"
SMTP_HOST_SETTING_KEY = "smtp_host"
SMTP_PORT_SETTING_KEY = "smtp_port"
SMTP_USERNAME_SETTING_KEY = "smtp_username"
SMTP_PASSWORD_SETTING_KEY = "smtp_password"
SMTP_FROM_EMAIL_SETTING_KEY = "smtp_from_email"
SMTP_SECURITY_SETTING_KEY = "smtp_security"
IMAP_HOST_SETTING_KEY = "imap_host"
IMAP_PORT_SETTING_KEY = "imap_port"
IMAP_USERNAME_SETTING_KEY = "imap_username"
IMAP_PASSWORD_SETTING_KEY = "imap_password"
IMAP_SECURITY_SETTING_KEY = "imap_security"
IMAP_MAILBOX_SETTING_KEY = "imap_mailbox"
INBOUND_MAIL_ENABLED_SETTING_KEY = "inbound_mail_enabled"
OUTBOUND_MAIL_ENABLED_SETTING_KEY = "outbound_mail_enabled"

MAIL_PROVIDER_PRESETS: dict[str, dict[str, object]] = {
    "custom": {},
    "local": {
        "smtp_host": "localhost",
        "smtp_port": 1025,
        "smtp_security": "none",
        "imap_host": "",
        "imap_port": 993,
        "imap_security": "ssl",
        "imap_mailbox": "INBOX",
    },
    "gmail": {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 465,
        "smtp_security": "ssl",
        "imap_host": "imap.gmail.com",
        "imap_port": 993,
        "imap_security": "ssl",
        "imap_mailbox": "INBOX",
    },
    "yandex": {
        "smtp_host": "smtp.yandex.com",
        "smtp_port": 465,
        "smtp_security": "ssl",
        "imap_host": "imap.yandex.com",
        "imap_port": 993,
        "imap_security": "ssl",
        "imap_mailbox": "INBOX",
    },
    "mailru": {
        "smtp_host": "smtp.mail.ru",
        "smtp_port": 465,
        "smtp_security": "ssl",
        "imap_host": "imap.mail.ru",
        "imap_port": 993,
        "imap_security": "ssl",
        "imap_mailbox": "INBOX",
    },
}


@dataclass(frozen=True)
class EmailPayload:
    recipient_email: str
    subject: str
    body: str


@dataclass(frozen=True)
class MailRuntimeSettings:
    provider_key: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_from_email: str
    smtp_security: str
    imap_host: str
    imap_port: int
    imap_username: str
    imap_password: str
    imap_security: str
    imap_mailbox: str
    inbound_mail_enabled: bool
    outbound_mail_enabled: bool


@dataclass(frozen=True)
class ReceivedEmail:
    mailbox_name: str
    message_uid: str
    message_id: str | None
    from_email: str | None
    from_name: str | None
    subject: str
    body_text: str
    received_at: str | None


def _setting_bool(database_path: Path, key: str, fallback: bool) -> bool:
    raw_value = get_system_setting(database_path, key)
    if raw_value is None:
        return fallback
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _setting_int(database_path: Path, key: str, fallback: int) -> int:
    raw_value = get_system_setting(database_path, key)
    if raw_value is None:
        return fallback
    try:
        return int(raw_value)
    except ValueError:
        return fallback


def get_effective_mail_settings(database_path: Path, settings: Settings) -> MailRuntimeSettings:
    provider_key = (
        get_system_setting(database_path, MAIL_PROVIDER_SETTING_KEY) or settings.mail_provider_key
    ).strip().lower() or "custom"
    return MailRuntimeSettings(
        provider_key=provider_key,
        smtp_host=(get_system_setting(database_path, SMTP_HOST_SETTING_KEY) or settings.smtp_host).strip(),
        smtp_port=_setting_int(database_path, SMTP_PORT_SETTING_KEY, settings.smtp_port),
        smtp_username=(get_system_setting(database_path, SMTP_USERNAME_SETTING_KEY) or settings.smtp_username).strip(),
        smtp_password=get_system_setting(database_path, SMTP_PASSWORD_SETTING_KEY) or settings.smtp_password,
        smtp_from_email=(
            get_system_setting(database_path, SMTP_FROM_EMAIL_SETTING_KEY) or settings.smtp_from_email
        ).strip(),
        smtp_security=(
            get_system_setting(database_path, SMTP_SECURITY_SETTING_KEY) or settings.smtp_security
        ).strip().lower()
        or "none",
        imap_host=(get_system_setting(database_path, IMAP_HOST_SETTING_KEY) or settings.imap_host).strip(),
        imap_port=_setting_int(database_path, IMAP_PORT_SETTING_KEY, settings.imap_port),
        imap_username=(get_system_setting(database_path, IMAP_USERNAME_SETTING_KEY) or settings.imap_username).strip(),
        imap_password=get_system_setting(database_path, IMAP_PASSWORD_SETTING_KEY) or settings.imap_password,
        imap_security=(
            get_system_setting(database_path, IMAP_SECURITY_SETTING_KEY) or settings.imap_security
        ).strip().lower()
        or "ssl",
        imap_mailbox=(
            get_system_setting(database_path, IMAP_MAILBOX_SETTING_KEY) or settings.imap_mailbox
        ).strip()
        or "INBOX",
        inbound_mail_enabled=_setting_bool(
            database_path,
            INBOUND_MAIL_ENABLED_SETTING_KEY,
            settings.inbound_mail_enabled,
        ),
        outbound_mail_enabled=_setting_bool(
            database_path,
            OUTBOUND_MAIL_ENABLED_SETTING_KEY,
            settings.outbound_mail_enabled,
        ),
    )


def persist_mail_settings(
    database_path: Path,
    settings: Settings,
    payload: dict[str, str],
    *,
    updated_at: str,
) -> MailRuntimeSettings:
    current = get_effective_mail_settings(database_path, settings)
    provider_key = payload.get("provider_key", current.provider_key).strip().lower() or "custom"
    preset = MAIL_PROVIDER_PRESETS.get(provider_key, MAIL_PROVIDER_PRESETS["custom"])

    smtp_username = payload.get("smtp_username", current.smtp_username).strip()
    smtp_password = payload.get("smtp_password", "").strip() or current.smtp_password
    imap_username = payload.get("imap_username", current.imap_username).strip()
    imap_password = payload.get("imap_password", "").strip() or current.imap_password
    smtp_from_email = payload.get("smtp_from_email", current.smtp_from_email).strip() or smtp_username
    outbound_enabled = payload.get("outbound_mail_enabled", "") == "on"
    inbound_enabled = payload.get("inbound_mail_enabled", "") == "on"

    if provider_key == "custom":
        smtp_host = payload.get("smtp_host", current.smtp_host).strip()
        smtp_port = int(payload.get("smtp_port", str(current.smtp_port)).strip() or current.smtp_port)
        smtp_security = payload.get("smtp_security", current.smtp_security).strip().lower() or "none"
        imap_host = payload.get("imap_host", current.imap_host).strip()
        imap_port = int(payload.get("imap_port", str(current.imap_port)).strip() or current.imap_port)
        imap_security = payload.get("imap_security", current.imap_security).strip().lower() or "ssl"
        imap_mailbox = payload.get("imap_mailbox", current.imap_mailbox).strip() or "INBOX"
    else:
        smtp_host = str(preset.get("smtp_host", current.smtp_host)).strip()
        smtp_port = int(preset.get("smtp_port", current.smtp_port))
        smtp_security = str(preset.get("smtp_security", current.smtp_security)).strip().lower()
        imap_host = str(preset.get("imap_host", current.imap_host)).strip()
        imap_port = int(preset.get("imap_port", current.imap_port))
        imap_security = str(preset.get("imap_security", current.imap_security)).strip().lower()
        imap_mailbox = str(preset.get("imap_mailbox", current.imap_mailbox)).strip() or "INBOX"

    next_settings = MailRuntimeSettings(
        provider_key=provider_key,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_username=smtp_username,
        smtp_password=smtp_password,
        smtp_from_email=smtp_from_email,
        smtp_security=smtp_security,
        imap_host=imap_host,
        imap_port=imap_port,
        imap_username=imap_username,
        imap_password=imap_password,
        imap_security=imap_security,
        imap_mailbox=imap_mailbox,
        inbound_mail_enabled=inbound_enabled,
        outbound_mail_enabled=outbound_enabled,
    )

    key_map = {
        MAIL_PROVIDER_SETTING_KEY: next_settings.provider_key,
        SMTP_HOST_SETTING_KEY: next_settings.smtp_host,
        SMTP_PORT_SETTING_KEY: str(next_settings.smtp_port),
        SMTP_USERNAME_SETTING_KEY: next_settings.smtp_username,
        SMTP_PASSWORD_SETTING_KEY: next_settings.smtp_password,
        SMTP_FROM_EMAIL_SETTING_KEY: next_settings.smtp_from_email,
        SMTP_SECURITY_SETTING_KEY: next_settings.smtp_security,
        IMAP_HOST_SETTING_KEY: next_settings.imap_host,
        IMAP_PORT_SETTING_KEY: str(next_settings.imap_port),
        IMAP_USERNAME_SETTING_KEY: next_settings.imap_username,
        IMAP_PASSWORD_SETTING_KEY: next_settings.imap_password,
        IMAP_SECURITY_SETTING_KEY: next_settings.imap_security,
        IMAP_MAILBOX_SETTING_KEY: next_settings.imap_mailbox,
        INBOUND_MAIL_ENABLED_SETTING_KEY: "1" if next_settings.inbound_mail_enabled else "0",
        OUTBOUND_MAIL_ENABLED_SETTING_KEY: "1" if next_settings.outbound_mail_enabled else "0",
    }
    for key, value in key_map.items():
        set_system_setting(
            database_path,
            key=key,
            value=value,
            updated_at=updated_at,
        )

    return next_settings


class SmtpEmailSender:
    def __init__(self, settings: Settings, *, database_path: Path | None = None):
        self._settings = settings
        self._database_path = database_path

    def send(self, payload: EmailPayload) -> None:
        runtime_settings = (
            get_effective_mail_settings(self._database_path, self._settings)
            if self._database_path is not None
            else MailRuntimeSettings(
                provider_key=self._settings.mail_provider_key,
                smtp_host=self._settings.smtp_host,
                smtp_port=self._settings.smtp_port,
                smtp_username=self._settings.smtp_username,
                smtp_password=self._settings.smtp_password,
                smtp_from_email=self._settings.smtp_from_email,
                smtp_security=self._settings.smtp_security,
                imap_host=self._settings.imap_host,
                imap_port=self._settings.imap_port,
                imap_username=self._settings.imap_username,
                imap_password=self._settings.imap_password,
                imap_security=self._settings.imap_security,
                imap_mailbox=self._settings.imap_mailbox,
                inbound_mail_enabled=self._settings.inbound_mail_enabled,
                outbound_mail_enabled=self._settings.outbound_mail_enabled,
            )
        )
        if not runtime_settings.outbound_mail_enabled:
            raise RuntimeError("Outbound mail is disabled")

        message = EmailMessage()
        message["From"] = runtime_settings.smtp_from_email
        message["To"] = payload.recipient_email
        message["Subject"] = payload.subject
        message.set_content(payload.body)

        if runtime_settings.smtp_security == "ssl":
            with smtplib.SMTP_SSL(
                runtime_settings.smtp_host,
                runtime_settings.smtp_port,
                timeout=30,
            ) as server:
                if runtime_settings.smtp_username:
                    server.login(runtime_settings.smtp_username, runtime_settings.smtp_password)
                server.send_message(message)
            return

        with smtplib.SMTP(runtime_settings.smtp_host, runtime_settings.smtp_port, timeout=30) as server:
            if runtime_settings.smtp_security == "starttls":
                server.starttls()

            if runtime_settings.smtp_username:
                server.login(runtime_settings.smtp_username, runtime_settings.smtp_password)

            server.send_message(message)


class ImapMailReceiver:
    def __init__(self, settings: Settings, *, database_path: Path):
        self._settings = settings
        self._database_path = database_path

    def fetch_unseen(self, *, limit: int = 20) -> list[ReceivedEmail]:
        runtime_settings = get_effective_mail_settings(self._database_path, self._settings)
        if not runtime_settings.inbound_mail_enabled:
            return []
        if not runtime_settings.imap_host or not runtime_settings.imap_username:
            return []

        client: imaplib.IMAP4 | imaplib.IMAP4_SSL
        if runtime_settings.imap_security == "ssl":
            client = imaplib.IMAP4_SSL(runtime_settings.imap_host, runtime_settings.imap_port)
        else:
            client = imaplib.IMAP4(runtime_settings.imap_host, runtime_settings.imap_port)

        try:
            client.login(runtime_settings.imap_username, runtime_settings.imap_password)
            status, _ = client.select(runtime_settings.imap_mailbox)
            if status != "OK":
                raise RuntimeError("Unable to select IMAP mailbox")

            status, search_data = client.uid("search", None, "UNSEEN")
            if status != "OK":
                raise RuntimeError("Unable to search IMAP mailbox")
            raw_uids = [uid for uid in (search_data[0] or b"").split() if uid]
            selected_uids = raw_uids[-limit:]
            emails: list[ReceivedEmail] = []

            for uid in selected_uids:
                fetch_status, message_data = client.uid("fetch", uid, "(RFC822)")
                if fetch_status != "OK":
                    continue

                raw_message = b""
                for item in message_data:
                    if isinstance(item, tuple) and len(item) > 1:
                        raw_message = item[1]
                        break
                if not raw_message:
                    continue

                parsed_message = BytesParser(policy=policy.default).parsebytes(raw_message)
                sender_name, sender_email = email.utils.parseaddr(str(parsed_message.get("From", "")))
                subject = str(make_header(decode_header(str(parsed_message.get("Subject", "")))))
                body_text = _extract_message_body(parsed_message).strip()
                emails.append(
                    ReceivedEmail(
                        mailbox_name=runtime_settings.imap_mailbox,
                        message_uid=uid.decode("utf-8", errors="ignore"),
                        message_id=str(parsed_message.get("Message-ID") or "").strip() or None,
                        from_email=sender_email or None,
                        from_name=sender_name or None,
                        subject=subject or "Без темы",
                        body_text=body_text,
                        received_at=str(parsed_message.get("Date") or "").strip() or None,
                    )
                )
                client.uid("store", uid, "+FLAGS", "(\\Seen)")
            return emails
        finally:
            try:
                client.close()
            except Exception:
                pass
            try:
                client.logout()
            except Exception:
                pass


def _extract_message_body(message: EmailMessage) -> str:
    if message.is_multipart():
        parts: list[str] = []
        for part in message.iter_parts():
            content_disposition = str(part.get("Content-Disposition") or "").lower()
            if "attachment" in content_disposition:
                continue
            parts.append(_extract_message_body(part))
        return "\n".join(part for part in parts if part.strip())

    if message.get_content_type() == "text/plain":
        return message.get_content()
    if message.get_content_type() == "text/html":
        return message.get_content()
    return ""


def get_mail_settings_debug_snapshot(database_path: Path, settings: Settings) -> dict[str, object]:
    runtime_settings = get_effective_mail_settings(database_path, settings)
    snapshot = asdict(runtime_settings)
    snapshot["smtp_password"] = "***" if runtime_settings.smtp_password else ""
    snapshot["imap_password"] = "***" if runtime_settings.imap_password else ""
    return snapshot
