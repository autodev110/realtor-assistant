from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Optional, Sequence

from core.config import get_settings
from core.storage.models import Client, Listing


NUMERIC_FEATURES = [
    "price",
    "sqft",
    "beds",
    "baths",
    "lot_sqft",
    "year_built",
    "hoa_fee",
    "days_on_market",
]

TAG_FEATURES = [
    "has_garage",
    "has_pool",
    "new_construction",
    "walkable",
    "open_floorplan",
    "finished_basement",
    "large_yard",
    "waterfront",
]

EXPLICIT_PREF_KEYS = {
    "price_min",
    "price_max",
    "beds_min",
    "beds_max",
    "baths_min",
    "baths_max",
    "neighborhoods",
    "counties",
    "must_have",
    "avoid",
}


@dataclass
class FeatureVector:
    numeric: Dict[str, float] = field(default_factory=dict)
    tags: Dict[str, float] = field(default_factory=dict)


@dataclass
class PreferenceVector:
    numeric: Dict[str, float] = field(default_factory=dict)
    tags: Dict[str, float] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def as_dict(self) -> Dict:
        return {
            "numeric": self.numeric,
            "tags": self.tags,
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_client(cls, client: Client) -> "PreferenceVector":
        raw = client.preference_vector or {}
        updated_at = datetime.utcnow()
        if isinstance(raw, dict):
            ts = raw.get("updated_at")
            if ts:
                try:
                    updated_at = datetime.fromisoformat(ts)
                except ValueError:
                    updated_at = datetime.utcnow()
        return cls(
            numeric=dict(raw.get("numeric", {})),
            tags=dict(raw.get("tags", {})),
            updated_at=updated_at,
        )


def _normalize(value: Optional[float], default: float = 0.0) -> float:
    if value is None:
        return default
    return float(value)


def _bool_as_float(value: Optional[bool]) -> float:
    return 1.0 if value else 0.0


def vector_from_listing(listing: Listing, explicit_prefs: Dict) -> FeatureVector:
    price_cents = listing.list_price_cents or listing.market_estimate_cents
    prefs = explicit_prefs or {}
    price_target = None
    price_band = prefs.get("price")
    if isinstance(price_band, list) and len(price_band) == 2:
        price_target = sum(price_band) / 2
    elif prefs.get("price_max") and prefs.get("price_min"):
        price_target = (prefs["price_min"] + prefs["price_max"]) / 2
    elif price_cents:
        price_target = price_cents / 100

    vector = FeatureVector(
        numeric={
            "price": _normalize(price_target or (price_cents or 0) / 100_00),
            "sqft": _normalize(listing.sqft, 0) / 4000.0,
            "beds": _normalize(listing.beds, 0),
            "baths": _normalize(listing.baths, 0),
            "lot_sqft": _normalize(listing.lot_sqft, 0) / 20000.0,
            "year_built": (_normalize(listing.year_built, datetime.utcnow().year) - 1950)
            / 100.0,
            "hoa_fee": _normalize(listing.hoa_fee_cents, 0) / 100_00,
            "days_on_market": _normalize(listing.days_on_market, 0) / 120.0,
        },
        tags={
            "has_garage": _bool_as_float((listing.amenities or {}).get("garage"))
            or _normalize(listing.parking_spaces, 0),
            "has_pool": _bool_as_float((listing.amenities or {}).get("pool")),
            "new_construction": _bool_as_float(
                listing.year_built and listing.year_built >= datetime.utcnow().year - 3
            ),
            "walkable": _bool_as_float(
                (listing.amenities or {}).get("walkscore", 0) >= 70
                if isinstance((listing.amenities or {}).get("walkscore"), (int, float))
                else False
            ),
            "open_floorplan": 1.0 if "open_floorplan" in (listing.features or []) else 0.0,
            "finished_basement": 1.0 if "finished_basement" in (listing.features or []) else 0.0,
            "large_yard": 1.0 if listing.lot_sqft and listing.lot_sqft >= 8000 else 0.0,
            "waterfront": 1.0 if (listing.features and "waterfront" in listing.features) else 0.0,
        },
    )
    return vector


def cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    if not vec_a or not vec_b:
        return 0.0
    numerator = sum(vec_a.get(k, 0.0) * vec_b.get(k, 0.0) for k in set(vec_a) | set(vec_b))
    denom_a = math.sqrt(sum(value * value for value in vec_a.values()))
    denom_b = math.sqrt(sum(value * value for value in vec_b.values()))
    if denom_a == 0 or denom_b == 0:
        return 0.0
    return numerator / (denom_a * denom_b)


def score_listing(listing_vector: FeatureVector, prefs: PreferenceVector) -> float:
    numeric_score = cosine_similarity(listing_vector.numeric, prefs.numeric)
    tag_score = cosine_similarity(listing_vector.tags, prefs.tags)
    return round(0.7 * numeric_score + 0.3 * tag_score, 4)


def apply_feedback(
    prefs: PreferenceVector,
    listing_vector: FeatureVector,
    signal_strength: float,
    learning_rate: Optional[float] = None,
) -> PreferenceVector:
    settings = get_settings()
    lr = learning_rate or settings.preference_learning_rate

    for key, value in listing_vector.numeric.items():
        current = prefs.numeric.get(key, 0.0)
        prefs.numeric[key] = current + lr * signal_strength * value

    for key, value in listing_vector.tags.items():
        current = prefs.tags.get(key, 0.0)
        prefs.tags[key] = current + lr * signal_strength * value

    prefs.updated_at = datetime.utcnow()
    return prefs


def decay_preferences(prefs: PreferenceVector, now: Optional[datetime] = None) -> PreferenceVector:
    settings = get_settings()
    now = now or datetime.utcnow()
    delta = now - prefs.updated_at
    if delta <= timedelta(days=settings.preference_decay_days):
        return prefs

    decay_factor = max(0.2, 1 - delta.days / (settings.preference_decay_days * 4))
    prefs.numeric = {k: v * decay_factor for k, v in prefs.numeric.items()}
    prefs.tags = {k: v * decay_factor for k, v in prefs.tags.items()}
    prefs.updated_at = now
    return prefs


def retrain_preferences(
    client: Client, listings: Iterable[Listing], interactions: Iterable[Dict[str, float]]
) -> PreferenceVector:
    prefs = PreferenceVector.from_client(client)
    explicit = client.prefs or {}
    decay_preferences(prefs)

    listing_index = {str(listing.id): listing for listing in listings}
    for interaction in interactions:
        listing = listing_index.get(interaction.get("listing_id"))
        if not listing:
            continue
        vector = vector_from_listing(listing, explicit)
        signal = interaction.get("signal", 0.0)
        apply_feedback(prefs, vector, signal)

    client.preference_vector = prefs.as_dict()
    return prefs
