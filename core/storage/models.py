from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship

from .types import GUID, UTCDateTime


Base = declarative_base()


def default_uuid() -> uuid.UUID:
    return uuid.uuid4()


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class Client(TimestampMixin, Base):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=default_uuid)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    phone: Mapped[Optional[str]] = mapped_column(String(32))
    tone_profile: Mapped[Dict] = mapped_column(JSON, default=dict, nullable=False)
    prefs: Mapped[Dict] = mapped_column(JSON, default=dict, nullable=False)
    preference_vector: Mapped[Dict] = mapped_column(JSON, default=dict, nullable=False)
    sentiment_profile: Mapped[Dict] = mapped_column(JSON, default=dict, nullable=False)
    auto_send_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    last_questionnaire_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime)
    last_interaction_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime)

    interactions: Mapped[List["Interaction"]] = relationship(
        "Interaction", back_populates="client", cascade="all, delete-orphan"
    )
    drafts: Mapped[List["DraftMessage"]] = relationship(
        "DraftMessage", back_populates="client", cascade="all, delete-orphan"
    )


class Listing(TimestampMixin, Base):
    __tablename__ = "listings"
    __table_args__ = (
        UniqueConstraint(
            "provider", "mls_id", "listing_key", name="uq_listing_provider_reference"
        ),
        Index("ix_listings_dedupe_key", "dedupe_key"),
        Index("ix_listings_status", "standard_status"),
        Index("ix_listings_county", "county"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=default_uuid)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    source_type: Mapped[str] = mapped_column(
        Enum("mls", "partner", "syndication", name="listing_source_type"),
        default="mls",
        nullable=False,
    )
    mls_id: Mapped[Optional[str]] = mapped_column(String(128))
    listing_key: Mapped[Optional[str]] = mapped_column(String(128))
    external_id: Mapped[Optional[str]] = mapped_column(String(128))
    dedupe_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    url: Mapped[Optional[str]] = mapped_column(String(512))
    address_line: Mapped[Optional[str]] = mapped_column(String(255))
    unit_number: Mapped[Optional[str]] = mapped_column(String(64))
    city: Mapped[Optional[str]] = mapped_column(String(128))
    state: Mapped[Optional[str]] = mapped_column(String(2))
    postal_code: Mapped[Optional[str]] = mapped_column(String(16))
    county: Mapped[Optional[str]] = mapped_column(String(128))
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    census_block: Mapped[Optional[str]] = mapped_column(String(32))
    school_district: Mapped[Optional[str]] = mapped_column(String(128))

    standard_status: Mapped[str] = mapped_column(String(64), nullable=False)
    status_raw: Mapped[Optional[str]] = mapped_column(String(128))
    property_type: Mapped[Optional[str]] = mapped_column(String(128))
    list_price_cents: Mapped[Optional[int]] = mapped_column(Integer)
    close_price_cents: Mapped[Optional[int]] = mapped_column(Integer)
    original_list_price_cents: Mapped[Optional[int]] = mapped_column(Integer)
    list_price_history: Mapped[List] = mapped_column(JSON, default=list, nullable=False)
    beds: Mapped[Optional[float]] = mapped_column(Float)
    baths: Mapped[Optional[float]] = mapped_column(Float)
    stories: Mapped[Optional[float]] = mapped_column(Float)
    sqft: Mapped[Optional[int]] = mapped_column(Integer)
    lot_sqft: Mapped[Optional[int]] = mapped_column(Integer)
    lot_acres: Mapped[Optional[float]] = mapped_column(Float)
    year_built: Mapped[Optional[int]] = mapped_column(Integer)
    parking_spaces: Mapped[Optional[int]] = mapped_column(Integer)
    hoa_fee_cents: Mapped[Optional[int]] = mapped_column(Integer)
    taxes_annual_cents: Mapped[Optional[int]] = mapped_column(Integer)
    days_on_market: Mapped[Optional[int]] = mapped_column(Integer)

    amenities: Mapped[Dict] = mapped_column(JSON, default=dict, nullable=False)
    features: Mapped[List] = mapped_column(JSON, default=list, nullable=False)
    condition_notes: Mapped[Dict] = mapped_column(JSON, default=dict, nullable=False)
    remarks: Mapped[Optional[str]] = mapped_column(Text)
    media: Mapped[List] = mapped_column(JSON, default=list, nullable=False)
    open_houses: Mapped[List] = mapped_column(JSON, default=list, nullable=False)
    provider_flags: Mapped[Dict] = mapped_column(JSON, default=dict, nullable=False)
    compliance_tags: Mapped[List] = mapped_column(JSON, default=list, nullable=False)
    risk_assessments: Mapped[Dict] = mapped_column(JSON, default=dict, nullable=False)
    source_payload: Mapped[Dict] = mapped_column(JSON, default=dict, nullable=False)

    listed_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime)
    expected_on_market_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime)
    source_updated_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime)
    expires_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime)
    off_market_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime)

    market_estimate_cents: Mapped[Optional[int]] = mapped_column(Integer)
    market_estimate_confidence: Mapped[Optional[float]] = mapped_column(Float)
    undervalue_ratio: Mapped[Optional[float]] = mapped_column(Float)

    comps_as_subject: Mapped[List["ComparableSale"]] = relationship(
        "ComparableSale",
        back_populates="subject",
        foreign_keys="ComparableSale.subject_listing_id",
        cascade="all, delete-orphan",
    )
    comps_as_comp: Mapped[List["ComparableSale"]] = relationship(
        "ComparableSale",
        back_populates="comparable",
        foreign_keys="ComparableSale.comp_listing_id",
        cascade="all, delete-orphan",
    )
    cma_reports: Mapped[List["CMAReport"]] = relationship(
        "CMAReport",
        back_populates="subject",
        cascade="all, delete-orphan",
    )


class ProviderIngestState(TimestampMixin, Base):
    __tablename__ = "provider_ingest_state"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=default_uuid)
    provider: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    last_cursor: Mapped[Optional[str]] = mapped_column(String(255))
    last_success_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime)
    last_error_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime)
    error_details: Mapped[Optional[Dict]] = mapped_column(JSON)


class Interaction(TimestampMixin, Base):
    __tablename__ = "interactions"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=default_uuid)
    client_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("clients.id"))
    listing_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID, ForeignKey("listings.id"))
    interaction_type: Mapped[str] = mapped_column(
        Enum(
            "email_open",
            "email_click",
            "like",
            "dislike",
            "reply_positive",
            "reply_negative",
            "questionnaire_completed",
            "note",
            name="interaction_type",
        ),
        nullable=False,
    )
    context: Mapped[Dict] = mapped_column(JSON, default=dict, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        UTCDateTime, nullable=False, default=datetime.utcnow
    )

    client: Mapped[Client] = relationship("Client", back_populates="interactions")
    listing: Mapped[Optional[Listing]] = relationship("Listing")


class PreferenceSnapshot(TimestampMixin, Base):
    __tablename__ = "preference_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=default_uuid)
    client_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("clients.id"))
    vector: Mapped[Dict] = mapped_column(JSON, default=dict, nullable=False)
    reason: Mapped[str] = mapped_column(String(128), nullable=False)
    client: Mapped[Client] = relationship("Client")


class DraftMessage(TimestampMixin, Base):
    __tablename__ = "draft_messages"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=default_uuid)
    client_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("clients.id"))
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    body_html: Mapped[Optional[str]] = mapped_column(Text)
    channel: Mapped[str] = mapped_column(
        Enum("email", "sms", "pdf", name="draft_channel"), nullable=False, default="email"
    )
    status: Mapped[str] = mapped_column(
        Enum(
            "draft",
            "pending_approval",
            "approved",
            "sent",
            "canceled",
            name="draft_status",
        ),
        nullable=False,
        default="draft",
    )
    listings_context: Mapped[List] = mapped_column(JSON, default=list, nullable=False)
    cma_report_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("cma_reports.id")
    )
    auto_send: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    scheduled_send_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime)
    sent_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime)
    context: Mapped[Dict] = mapped_column(JSON, default=dict, nullable=False)

    client: Mapped[Client] = relationship("Client", back_populates="drafts")
    cma_report: Mapped[Optional["CMAReport"]] = relationship("CMAReport")


class CMAReport(TimestampMixin, Base):
    __tablename__ = "cma_reports"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=default_uuid)
    subject_listing_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("listings.id"), nullable=False
    )
    params: Mapped[Dict] = mapped_column(JSON, default=dict, nullable=False)
    comps_summary: Mapped[List] = mapped_column(JSON, default=list, nullable=False)
    price_low_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    price_mid_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    price_high_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    psf_chart: Mapped[Dict] = mapped_column(JSON, default=dict, nullable=False)
    narrative: Mapped[str] = mapped_column(Text, nullable=False)
    pdf_storage_path: Mapped[Optional[str]] = mapped_column(String(512))
    report_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        UTCDateTime, nullable=False, default=datetime.utcnow
    )

    subject: Mapped[Listing] = relationship("Listing", back_populates="cma_reports")
    comparables: Mapped[List["ComparableSale"]] = relationship(
        "ComparableSale",
        back_populates="report",
        cascade="all, delete-orphan",
    )


class ComparableSale(TimestampMixin, Base):
    __tablename__ = "comparable_sales"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=default_uuid)
    report_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("cma_reports.id"))
    subject_listing_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("listings.id"), nullable=False
    )
    comp_listing_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("listings.id"), nullable=False
    )
    adjustments: Mapped[Dict] = mapped_column(JSON, default=dict, nullable=False)
    adjusted_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    distance_miles: Mapped[float] = mapped_column(Float, nullable=False)
    days_back: Mapped[int] = mapped_column(Integer, nullable=False)
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)

    report: Mapped[Optional[CMAReport]] = relationship("CMAReport", back_populates="comparables")
    subject: Mapped[Listing] = relationship(
        "Listing",
        foreign_keys=[subject_listing_id],
        back_populates="comps_as_subject",
    )
    comparable: Mapped[Listing] = relationship(
        "Listing",
        foreign_keys=[comp_listing_id],
        back_populates="comps_as_comp",
    )


class DealAlert(TimestampMixin, Base):
    __tablename__ = "deal_alerts"
    __table_args__ = (
        UniqueConstraint(
            "listing_id", "source_report_id", name="uq_deal_alert_listing_source"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=default_uuid)
    listing_id: Mapped[uuid.UUID] = mapped_column(GUID, ForeignKey("listings.id"), nullable=False)
    source_report_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("cma_reports.id"), nullable=False
    )
    market_value_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    list_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    discount_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    excluded_defects: Mapped[List] = mapped_column(JSON, default=list, nullable=False)
    acknowledged_by_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    admin_notes: Mapped[Optional[str]] = mapped_column(Text)

    listing: Mapped[Listing] = relationship("Listing")
    report: Mapped[CMAReport] = relationship("CMAReport")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=default_uuid)
    actor: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(255))
    payload: Mapped[Dict] = mapped_column(JSON, default=dict, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        UTCDateTime, nullable=False, default=datetime.utcnow
    )


class EmailEnvelope(TimestampMixin, Base):
    __tablename__ = "email_envelopes"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=default_uuid)
    message_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    sender: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(512), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        UTCDateTime, nullable=False, default=datetime.utcnow
    )
    raw_headers: Mapped[Dict] = mapped_column(JSON, default=dict, nullable=False)
    parsed_body: Mapped[str] = mapped_column(Text, nullable=False)
    is_spam: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    spam_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    client_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID, ForeignKey("clients.id"))
    classification: Mapped[Optional[str]] = mapped_column(
        Enum(
            "new_lead",
            "existing_client",
            "vendor",
            "spam",
            "unknown",
            name="email_classification",
        )
    )

    client: Mapped[Optional[Client]] = relationship("Client")
