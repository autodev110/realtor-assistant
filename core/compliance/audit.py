from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Dict, Optional

from core.storage.db import session_scope
from core.storage.models import AuditLog


REDACTED = "***"


def hash_email(email: Optional[str]) -> Optional[str]:
    if not email:
        return None
    digest = hashlib.sha256(email.lower().encode("utf-8")).hexdigest()[:12]
    return f"hash:{digest}"


def mask_phone(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None
    digits = "".join(filter(str.isdigit, phone))
    if len(digits) <= 4:
        return f"***{digits}"
    return f"{'*' * (len(digits) - 4)}{digits[-4:]}"


def redact_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    redacted: Dict[str, Any] = {}
    for key, value in payload.items():
        if value is None:
            redacted[key] = None
            continue
        lowered = key.lower()
        if "email" in lowered:
            redacted[key] = hash_email(str(value))
        elif "phone" in lowered:
            redacted[key] = mask_phone(str(value))
        elif any(token in lowered for token in ("ssn", "social_security", "password")):
            redacted[key] = REDACTED
        else:
            redacted[key] = value
    return redacted


def log_audit_event(
    *,
    actor: str,
    action: str,
    subject: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    occurred_at: Optional[datetime] = None,
) -> None:
    with session_scope() as session:
        session.add(
            AuditLog(
                actor=actor,
                action=action,
                subject=subject,
                payload=redact_payload(payload or {}),
                occurred_at=occurred_at or datetime.utcnow(),
            )
        )


def log_listing_export(actor: str, listing_ids: Dict[str, Any], destination: str) -> None:
    log_audit_event(
        actor=actor,
        action="LISTING_EXPORT",
        subject=",".join(listing_ids),
        payload={"destination": destination, "listing_ids": listing_ids},
    )
