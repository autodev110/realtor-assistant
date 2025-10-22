from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.schema.listing import NormalizedListing

from .models import DealAlert, Listing


MUTABLE_FIELDS = {
    "provider",
    "source_type",
    "mls_id",
    "listing_key",
    "external_id",
    "dedupe_key",
    "url",
    "address_line",
    "unit_number",
    "city",
    "state",
    "postal_code",
    "county",
    "latitude",
    "longitude",
    "census_block",
    "school_district",
    "standard_status",
    "status_raw",
    "property_type",
    "list_price_cents",
    "close_price_cents",
    "original_list_price_cents",
    "list_price_history",
    "beds",
    "baths",
    "stories",
    "sqft",
    "lot_sqft",
    "lot_acres",
    "year_built",
    "parking_spaces",
    "hoa_fee_cents",
    "taxes_annual_cents",
    "days_on_market",
    "amenities",
    "features",
    "condition_notes",
    "remarks",
    "media",
    "open_houses",
    "provider_flags",
    "compliance_tags",
    "risk_assessments",
    "listed_at",
    "expected_on_market_at",
    "last_seen_at",
    "source_updated_at",
    "expires_at",
    "off_market_at",
    "market_estimate_cents",
    "market_estimate_confidence",
    "undervalue_ratio",
    "source_payload",
}


def upsert_listing(session: Session, normalized: NormalizedListing) -> Listing:
    payload = normalized.to_orm_dict()
    stmt = select(Listing).where(Listing.dedupe_key == payload["dedupe_key"])
    existing: Optional[Listing] = session.execute(stmt).scalar_one_or_none()

    if existing:
        _update_listing(existing, payload)
        existing.last_seen_at = payload.get("last_seen_at") or datetime.utcnow()
        return existing

    listing = Listing(**payload)
    listing.last_seen_at = payload.get("last_seen_at") or datetime.utcnow()
    session.add(listing)
    return listing


def persist_deal_alert(
    session: Session, listing: Listing, deal_payload: Dict
) -> DealAlert:
    stmt = select(DealAlert).where(
        DealAlert.listing_id == listing.id,
        DealAlert.source_report_id == deal_payload["source_report_id"],
    )
    existing = session.execute(stmt).scalar_one_or_none()
    if existing:
        existing.market_value_cents = deal_payload["market_value_cents"]
        existing.list_price_cents = deal_payload["list_price_cents"]
        existing.discount_ratio = deal_payload["discount_ratio"]
        existing.rationale = deal_payload["rationale"]
        existing.excluded_defects = deal_payload.get("excluded_defects", [])
        existing.updated_at = datetime.utcnow()
        return existing

    alert = DealAlert(
        listing_id=listing.id,
        source_report_id=deal_payload["source_report_id"],
        market_value_cents=deal_payload["market_value_cents"],
        list_price_cents=deal_payload["list_price_cents"],
        discount_ratio=deal_payload["discount_ratio"],
        rationale=deal_payload["rationale"],
        excluded_defects=deal_payload.get("excluded_defects", []),
    )
    session.add(alert)
    return alert


def _update_listing(listing: Listing, payload: Dict) -> None:
    for field in MUTABLE_FIELDS:
        if field not in payload:
            continue
        new_value = payload[field]
        old_value = getattr(listing, field)
        if new_value == old_value:
            continue
        if field == "list_price_cents" and old_value and new_value and old_value != new_value:
            history = list(listing.list_price_history or [])
            history.append(
                {
                    "at": datetime.utcnow().isoformat(),
                    "previous": old_value,
                    "new": new_value,
                }
            )
            listing.list_price_history = history[-50:]
        setattr(listing, field, new_value)
