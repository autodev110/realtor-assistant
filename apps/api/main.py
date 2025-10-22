from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.compliance.audit import log_audit_event
from core.config import get_settings
from core.matching.preferences import retrain_preferences
from core.storage.db import SessionLocal, init_db
from infra.monitoring import register_instrumentation
from core.storage.models import (
    Client,
    DealAlert,
    DraftMessage,
    EmailEnvelope,
    Interaction,
    Listing,
    PreferenceSnapshot,
)


SETTINGS = get_settings()

app = FastAPI(title="Realtor Assistant API", version="1.0.0")
register_instrumentation(app)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def _startup() -> None:
    init_db()


class EmailWebhookPayload(BaseModel):
    message_id: str
    sender: str
    subject: str
    body: str
    received_at: datetime = Field(default_factory=datetime.utcnow)
    headers: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, str] = Field(default_factory=dict)


class DraftResponse(BaseModel):
    id: UUID
    subject: str
    status: str
    created_at: datetime
    listings: List[Dict]
    auto_send: bool
    scheduled_send_at: Optional[datetime]


class DealAlertResponse(BaseModel):
    id: UUID
    listing_id: UUID
    market_value_cents: int
    list_price_cents: int
    discount_ratio: float
    rationale: str
    acknowledged: bool
    created_at: datetime


class DealAlertAcknowledgeRequest(BaseModel):
    admin_notes: Optional[str] = None


class RetrainRequest(BaseModel):
    interactions: List[Dict[str, float]] = Field(default_factory=list)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


def _classify_email(payload: EmailWebhookPayload) -> str:
    sender_domain = payload.sender.split("@")[-1].lower()
    subject = payload.subject.lower()
    body = payload.body.lower()
    spam_keywords = ["unsubscribe", "lottery", "crypto", "viagra", "investment opportunity"]
    auto_reply_triggers = ["out of office", "auto-reply", "autoreply"]

    if any(keyword in body for keyword in spam_keywords):
        return "spam"
    if any(trigger in subject for trigger in auto_reply_triggers):
        return "spam"
    allowed_domains = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com"}
    if sender_domain not in allowed_domains:
        return "unknown"
    return "existing_client"


@app.post("/webhook/email", status_code=status.HTTP_202_ACCEPTED)
def email_webhook(payload: EmailWebhookPayload, db: Session = Depends(get_db)):
    classification = _classify_email(payload)
    envelope = EmailEnvelope(
        message_id=payload.message_id,
        sender=payload.sender,
        subject=payload.subject,
        raw_headers=payload.headers,
        parsed_body=payload.body,
        received_at=payload.received_at,
        is_spam=classification == "spam",
        spam_score=1.0 if classification == "spam" else 0.0,
        classification=classification,
    )
    client: Optional[Client] = None
    if classification != "spam":
        client = (
            db.query(Client)
            .filter(Client.email == payload.sender)
            .one_or_none()
        )
        if not client:
            client = Client(
                email=payload.sender,
                full_name=payload.sender.split("@")[0].replace(".", " ").title(),
                prefs={},
                tone_profile={},
            )
            db.add(client)
            db.flush()
        envelope.client = client
        client.last_interaction_at = datetime.utcnow()

    db.add(envelope)
    db.commit()

    log_audit_event(
        actor="webhook:email",
        action="EMAIL_RECEIVED",
        subject=payload.message_id,
        payload={"sender": payload.sender, "classification": classification},
    )

    return {"classification": classification, "client_id": str(client.id) if client else None}


@app.get("/clients/{client_id}/drafts", response_model=List[DraftResponse])
def list_drafts(client_id: UUID, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    drafts = (
        db.query(DraftMessage)
        .filter(DraftMessage.client_id == client_id)
        .order_by(DraftMessage.created_at.desc())
        .all()
    )
    return [
        DraftResponse(
            id=draft.id,
            subject=draft.subject,
            status=draft.status,
            created_at=draft.created_at,
            listings=draft.listings_context,
            auto_send=draft.auto_send,
            scheduled_send_at=draft.scheduled_send_at,
        )
        for draft in drafts
    ]


@app.get("/admin/deal-alerts", response_model=List[DealAlertResponse])
def list_deal_alerts(include_acknowledged: bool = False, db: Session = Depends(get_db)):
    query = db.query(DealAlert)
    if not include_acknowledged:
        query = query.filter(DealAlert.acknowledged_by_admin.is_(False))
    alerts = query.order_by(DealAlert.created_at.desc()).limit(100).all()
    return [
        DealAlertResponse(
            id=alert.id,
            listing_id=alert.listing_id,
            market_value_cents=alert.market_value_cents,
            list_price_cents=alert.list_price_cents,
            discount_ratio=alert.discount_ratio,
            rationale=alert.rationale,
            acknowledged=alert.acknowledged_by_admin,
            created_at=alert.created_at,
        )
        for alert in alerts
    ]


@app.post("/admin/deal-alerts/{alert_id}/acknowledge")
def acknowledge_deal_alert(alert_id: UUID, request: DealAlertAcknowledgeRequest, db: Session = Depends(get_db)):
    alert = db.query(DealAlert).filter(DealAlert.id == alert_id).one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Deal alert not found")
    alert.acknowledged_by_admin = True
    alert.admin_notes = request.admin_notes
    alert.updated_at = datetime.utcnow()
    db.commit()
    log_audit_event(
        actor="admin",
        action="DEAL_ALERT_ACK",
        subject=str(alert_id),
        payload={"admin_notes": request.admin_notes},
    )
    return {"status": "acknowledged"}


@app.post("/clients/{client_id}/drafts/{draft_id}/send", status_code=status.HTTP_202_ACCEPTED)
def approve_draft(client_id: UUID, draft_id: UUID, db: Session = Depends(get_db)):
    draft = (
        db.query(DraftMessage)
        .filter(DraftMessage.id == draft_id, DraftMessage.client_id == client_id)
        .one_or_none()
    )
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft.status not in {"draft", "pending_approval"}:
        raise HTTPException(status_code=400, detail=f"Draft already {draft.status}")
    draft.status = "approved"
    draft.sent_at = datetime.utcnow()
    db.commit()
    log_audit_event(
        actor="agent",
        action="DRAFT_APPROVED",
        subject=str(draft_id),
        payload={"client_id": str(client_id), "channel": draft.channel},
    )
    return {"status": "approved"}


@app.post("/clients/{client_id}/retrain")
def retrain(client_id: UUID, request: RetrainRequest, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    interactions = (
        db.query(Interaction)
        .filter(Interaction.client_id == client_id)
        .order_by(Interaction.occurred_at.desc())
        .limit(250)
        .all()
    )
    interaction_payload = [
        {"listing_id": str(ix.listing_id), "signal": ix.metadata.get("signal", 0.0)}
        for ix in interactions
        if ix.listing_id
    ]
    if request.interactions:
        interaction_payload.extend(request.interactions)

    listing_ids = {item["listing_id"] for item in interaction_payload if item.get("listing_id")}
    listings = (
        db.query(Listing)
        .filter(Listing.id.in_(listing_ids))
        .all()
        if listing_ids
        else []
    )

    prefs = retrain_preferences(client, listings, interaction_payload)
    db.add(
        PreferenceSnapshot(
            client_id=client.id, vector=prefs.as_dict(), reason="manual-retrain"
        )
    )
    db.commit()
    return {"status": "ok", "updated_at": prefs.updated_at.isoformat()}
