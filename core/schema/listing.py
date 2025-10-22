from __future__ import annotations

import re
import unicodedata
import uuid
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


def _to_cents(value: Optional[float]) -> Optional[int]:
    if value is None:
        return None
    quantized = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return int(quantized * 100)


def slugify(value: str) -> str:
    normalized = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    return normalized.strip("-")


def build_dedupe_key(
    provider: str,
    mls_id: Optional[str],
    listing_key: Optional[str],
    external_id: Optional[str],
    address_line: Optional[str],
    postal_code: Optional[str],
) -> str:
    parts = [provider.lower().strip()]
    for candidate in (mls_id, listing_key, external_id):
        cleaned = (candidate or "").strip().lower()
        if cleaned:
            parts.append(cleaned)
    if len(parts) == 1 and address_line:
        parts.append(slugify(address_line))
        if postal_code:
            parts.append(postal_code.lower().strip())
    key = "|".join(parts)
    if not key:
        raise ValueError("Unable to compute dedupe key for listing")
    return key


class MediaAsset(BaseModel):
    url: HttpUrl
    caption: Optional[str] = None
    attribution: Optional[str] = None
    license: Optional[str] = None
    is_primary: bool = False


class NormalizedListing(BaseModel):
    provider: str
    source_type: str = Field(default="mls")
    mls_id: Optional[str] = None
    listing_key: Optional[str] = None
    external_id: Optional[str] = None
    url: Optional[HttpUrl] = None
    address_line: Optional[str] = Field(default=None, alias="address")
    unit_number: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    county: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    census_block: Optional[str] = None
    school_district: Optional[str] = None

    standard_status: str
    status_raw: Optional[str] = None
    property_type: Optional[str] = None

    list_price: Optional[float] = None
    close_price: Optional[float] = None
    original_list_price: Optional[float] = None
    list_price_history: List[Dict[str, Any]] = Field(default_factory=list)
    beds: Optional[float] = None
    baths: Optional[float] = None
    stories: Optional[float] = None
    sqft: Optional[int] = None
    lot_sqft: Optional[int] = None
    lot_acres: Optional[float] = None
    year_built: Optional[int] = None
    parking_spaces: Optional[int] = None
    hoa_fee: Optional[float] = None
    taxes_annual: Optional[float] = None
    days_on_market: Optional[int] = None
    amenities: Dict[str, Any] = Field(default_factory=dict)
    features: List[str] = Field(default_factory=list)
    condition_notes: Dict[str, Any] = Field(default_factory=dict)
    remarks: Optional[str] = None
    media: List[MediaAsset] = Field(default_factory=list)
    open_houses: List[Dict[str, Any]] = Field(default_factory=list)
    provider_flags: Dict[str, Any] = Field(default_factory=dict)
    compliance_tags: List[str] = Field(default_factory=list)
    risk_assessments: Dict[str, Any] = Field(default_factory=dict)

    listed_at: Optional[datetime] = None
    expected_on_market_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    source_updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    off_market_at: Optional[datetime] = None

    market_estimate: Optional[float] = None
    market_estimate_confidence: Optional[float] = None
    undervalue_ratio: Optional[float] = None

    source_payload: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True

    def to_orm_dict(self) -> Dict[str, Any]:
        dedupe_key = build_dedupe_key(
            provider=self.provider,
            mls_id=self.mls_id,
            listing_key=self.listing_key,
            external_id=self.external_id,
            address_line=self.address_line,
            postal_code=self.postal_code,
        )
        return {
            "provider": self.provider.lower(),
            "source_type": self.source_type,
            "mls_id": (self.mls_id or "").strip() or None,
            "listing_key": (self.listing_key or "").strip() or None,
            "external_id": (self.external_id or "").strip() or None,
            "dedupe_key": dedupe_key,
            "url": str(self.url) if self.url else None,
            "address_line": self.address_line,
            "unit_number": self.unit_number,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "county": self.county,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "census_block": self.census_block,
            "school_district": self.school_district,
            "standard_status": self.standard_status,
            "status_raw": self.status_raw,
            "property_type": self.property_type,
            "list_price_cents": _to_cents(self.list_price),
            "close_price_cents": _to_cents(self.close_price),
            "original_list_price_cents": _to_cents(self.original_list_price),
            "list_price_history": self.list_price_history,
            "beds": self.beds,
            "baths": self.baths,
            "stories": self.stories,
            "sqft": self.sqft,
            "lot_sqft": self.lot_sqft,
            "lot_acres": self.lot_acres,
            "year_built": self.year_built,
            "parking_spaces": self.parking_spaces,
            "hoa_fee_cents": _to_cents(self.hoa_fee),
            "taxes_annual_cents": _to_cents(self.taxes_annual),
            "days_on_market": self.days_on_market,
            "amenities": self.amenities,
            "features": self.features,
            "condition_notes": self.condition_notes,
            "remarks": self.remarks,
            "media": [asset.model_dump(mode="json") for asset in self.media],
            "open_houses": self.open_houses,
            "provider_flags": self.provider_flags,
            "compliance_tags": self.compliance_tags,
            "risk_assessments": self.risk_assessments,
            "listed_at": self.listed_at,
            "expected_on_market_at": self.expected_on_market_at,
            "last_seen_at": self.last_seen_at,
            "source_updated_at": self.source_updated_at,
            "expires_at": self.expires_at,
            "off_market_at": self.off_market_at,
            "market_estimate_cents": _to_cents(self.market_estimate),
            "market_estimate_confidence": self.market_estimate_confidence,
            "undervalue_ratio": self.undervalue_ratio,
            "source_payload": self.source_payload,
        }


class DealAlertPayload(BaseModel):
    listing_id: uuid.UUID
    source_report_id: uuid.UUID
    market_value_cents: int
    list_price_cents: int
    discount_ratio: float
    rationale: str
    excluded_defects: List[str] = Field(default_factory=list)
