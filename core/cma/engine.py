from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from core.config import get_settings
from core.schema.listing import DealAlertPayload
from core.storage.models import Listing


BED_ADJUST_CENTS = 1_200_000  # $12k
BATH_ADJUST_CENTS = 800_000  # $8k
GARAGE_ADJUST_CENTS = 800_000  # $8k
POOL_ADJUST_CENTS = 2_000_000  # $20k
YEAR_ADJUST_CENTS = 100_000  # $1k per year difference


@dataclass
class CMAComp:
    listing_id: str
    raw_price_cents: int
    adjusted_price_cents: int
    adjustments: Dict[str, int]
    distance_miles: float
    days_back: int
    psf: Optional[float]
    similarity_score: float


@dataclass
class CMAResult:
    price_low_cents: int
    price_mid_cents: int
    price_high_cents: int
    confidence: float
    comps: List[CMAComp]
    psf_chart: List[Dict[str, float]]
    deal_alert: Optional[DealAlertPayload]


def price_per_sqft_cents(listing: Listing) -> Optional[float]:
    sqft = listing.sqft or 0
    if sqft <= 0:
        return None
    price = listing.close_price_cents or listing.list_price_cents
    if not price:
        return None
    return price / sqft


def _adjust_price(subject: Listing, comp: Listing, baseline_psf: float) -> Tuple[int, Dict[str, int]]:
    base_price = comp.close_price_cents or comp.list_price_cents
    if not base_price:
        raise ValueError("Comparable listing is missing price information")

    adjustments: Dict[str, int] = {}
    price_cents = base_price

    bed_delta = (subject.beds or 0) - (comp.beds or 0)
    if bed_delta:
        adjustments["bedrooms"] = int(bed_delta * BED_ADJUST_CENTS)
        price_cents += adjustments["bedrooms"]

    bath_delta = (subject.baths or 0) - (comp.baths or 0)
    if bath_delta:
        adjustments["bathrooms"] = int(bath_delta * BATH_ADJUST_CENTS)
        price_cents += adjustments["bathrooms"]

    if subject.sqft and comp.sqft:
        sqft_delta = subject.sqft - comp.sqft
        adjustments["living_area"] = int(sqft_delta * baseline_psf)
        price_cents += adjustments["living_area"]

    if subject.lot_sqft and comp.lot_sqft:
        lot_delta = subject.lot_sqft - comp.lot_sqft
        lot_adjust_per_sqft = baseline_psf * 0.15
        adjustments["lot_size"] = int(lot_delta * lot_adjust_per_sqft)
        price_cents += adjustments["lot_size"]

    if subject.parking_spaces and not comp.parking_spaces:
        adjustments["garage"] = GARAGE_ADJUST_CENTS
        price_cents += adjustments["garage"]
    elif comp.parking_spaces and not subject.parking_spaces:
        adjustments["garage"] = -GARAGE_ADJUST_CENTS
        price_cents += adjustments["garage"]

    subject_pool = (subject.amenities or {}).get("pool") or (subject.features and "pool" in subject.features)
    comp_pool = (comp.amenities or {}).get("pool") or (comp.features and "pool" in comp.features)
    if subject_pool and not comp_pool:
        adjustments["pool"] = POOL_ADJUST_CENTS
        price_cents += adjustments["pool"]
    elif comp_pool and not subject_pool:
        adjustments["pool"] = -POOL_ADJUST_CENTS
        price_cents += adjustments["pool"]

    if subject.year_built and comp.year_built:
        year_delta = subject.year_built - comp.year_built
        adjustments["year_built"] = int(year_delta * YEAR_ADJUST_CENTS)
        price_cents += adjustments["year_built"]

    return max(price_cents, 0), adjustments


def _confidence_from_prices(adjusted_prices: Sequence[int], comps: Sequence[Listing]) -> float:
    if not adjusted_prices:
        return 0.0
    median = statistics.median(adjusted_prices)
    if median <= 0:
        return 0.0
    mad = statistics.median([abs(p - median) for p in adjusted_prices])
    variability = mad / median if median else 0
    size_factor = min(1.0, len(adjusted_prices) / 6)
    confidence = max(0.2, min(0.95, size_factor * (1 - variability)))
    recent_factor = 1.0
    if comps:
        recent_days = [max(1, comp.days_on_market or 1) for comp in comps]
        recent_factor = max(0.8, min(1.0, statistics.mean(recent_days) / 180))
    return round(confidence * recent_factor, 2)


def _detect_deal(subject: Listing, price_mid_cents: int) -> Optional[DealAlertPayload]:
    settings = get_settings()
    list_price_cents = subject.list_price_cents
    if not list_price_cents or price_mid_cents <= 0:
        return None
    ratio = list_price_cents / price_mid_cents
    if ratio > settings.deal_discount_threshold:
        return None

    issues = set()
    for key in ("mechanical", "electrical", "structural"):
        note_value = (subject.condition_notes or {}).get(key)
        if note_value:
            issues.add(key)
    if issues:
        return None

    return DealAlertPayload(
        listing_id=subject.id,
        source_report_id=subject.id,  # placeholder — will be overwritten by caller
        market_value_cents=price_mid_cents,
        list_price_cents=list_price_cents,
        discount_ratio=round(ratio, 4),
        rationale=f"Priced {round((1 - ratio) * 100, 1)}% below median CMA estimate.",
        excluded_defects=[],
    )


def compute_cma(subject: Listing, comparables: Iterable[Tuple[Listing, float, int]]) -> CMAResult:
    entries = list(comparables)
    comps: List[CMAComp] = []
    psf_values: List[float] = []
    adjusted_prices: List[int] = []

    for comp_listing, distance, days_back in entries:
        psf = price_per_sqft_cents(comp_listing)
        if psf:
            psf_values.append(psf)

    baseline_psf = statistics.mean(psf_values) if psf_values else (
        subject.list_price_cents / subject.sqft if subject.sqft and subject.list_price_cents else 0
    )

    for comp_listing, distance, days_back in entries:
        try:
            adjusted_price, adjustments = _adjust_price(subject, comp_listing, baseline_psf)
        except ValueError:
            continue
        base_price = comp_listing.close_price_cents or comp_listing.list_price_cents or 0
        psf = price_per_sqft_cents(comp_listing)
        similarity_score = _compute_similarity(subject, comp_listing)
        comps.append(
            CMAComp(
                listing_id=str(comp_listing.id),
                raw_price_cents=base_price,
                adjusted_price_cents=adjusted_price,
                adjustments=adjustments,
                distance_miles=distance,
                days_back=days_back,
                psf=psf / 100 if psf else None,
                similarity_score=similarity_score,
            )
        )
        adjusted_prices.append(adjusted_price)

    if not adjusted_prices:
        raise ValueError("No valid comparable sales provided")

    price_mid = int(statistics.median(adjusted_prices))
    mad = statistics.median([abs(p - price_mid) for p in adjusted_prices]) or price_mid * 0.05
    band_radius = int(1.4826 * mad)

    price_low = max(price_mid - band_radius, 0)
    price_high = price_mid + band_radius
    confidence = _confidence_from_prices(adjusted_prices, [comp for comp, _, _ in entries])

    psf_chart = []
    for comp in comps:
        if comp.psf:
            psf_chart.append(
                {
                    "listing_id": comp.listing_id,
                    "price_per_sqft": round(comp.psf, 2),
                }
            )

    deal_alert = _detect_deal(subject, price_mid)

    return CMAResult(
        price_low_cents=price_low,
        price_mid_cents=price_mid,
        price_high_cents=price_high,
        confidence=confidence,
        comps=comps,
        psf_chart=psf_chart,
        deal_alert=deal_alert,
    )


def _compute_similarity(subject: Listing, comp: Listing) -> float:
    weights = {
        "beds": 0.2,
        "baths": 0.2,
        "sqft": 0.25,
        "lot": 0.1,
        "year": 0.1,
        "distance": 0.15,
    }

    def ratio_diff(subject_value, comp_value) -> float:
        if not subject_value or not comp_value:
            return 0.0
        denominator = max(subject_value, comp_value)
        return abs(subject_value - comp_value) / denominator

    bed_score = 1 - ratio_diff(subject.beds, comp.beds)
    bath_score = 1 - ratio_diff(subject.baths, comp.baths)
    sqft_score = 1 - ratio_diff(subject.sqft, comp.sqft)
    lot_score = 1 - ratio_diff(subject.lot_sqft, comp.lot_sqft)
    year_score = 1 - ratio_diff(subject.year_built, comp.year_built)

    distance_score = 1.0
    # distance considered by caller; placeholder for weighting

    composite = (
        bed_score * weights["beds"]
        + bath_score * weights["baths"]
        + sqft_score * weights["sqft"]
        + lot_score * weights["lot"]
        + year_score * weights["year"]
        + distance_score * weights["distance"]
    )
    return max(0.0, min(1.0, composite))
