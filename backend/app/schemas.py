from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator


EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class RequestAccessPayload(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    organization: str | None = Field(default=None, max_length=200)
    position: str | None = Field(default=None, max_length=200)
    email: str = Field(min_length=3, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    purpose: str = Field(min_length=10, max_length=2000)
    format: Literal["electronic", "paper", "both"]
    consent: bool

    @field_validator("first_name", "last_name", "organization", "position", "phone", "purpose")
    @classmethod
    def strip_values(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        email = value.strip().lower()
        if not EMAIL_RE.match(email):
            raise ValueError("Invalid email format")
        return email

    @field_validator("consent")
    @classmethod
    def require_consent(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Consent is required")
        return value


class RequestAccessResponse(BaseModel):
    status: Literal["accepted"]
    request_id: int
    electronic_status: Literal["none", "pending", "sent", "failed"]
    paper_status: Literal["none", "review", "approved", "rejected"]
    email_job_id: int | None = None
    delivery_scheduled_for: str | None = None
