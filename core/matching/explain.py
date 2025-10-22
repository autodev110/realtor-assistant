from __future__ import annotations

from typing import Dict, List

from .preferences import FeatureVector, PreferenceVector


LABEL_MAP: Dict[str, str] = {
    "price": "Aligned with price range",
    "sqft": "Comfortable square footage",
    "beds": "Bedroom count match",
    "baths": "Bathroom count match",
    "lot_sqft": "Lot size fit",
    "year_built": "Desired vintage",
    "hoa_fee": "Low HOA fees",
    "days_on_market": "Fresh on market",
    "has_garage": "Garage / parking",
    "has_pool": "Pool amenity",
    "new_construction": "Newer construction",
    "walkable": "Walkable location",
    "open_floorplan": "Open floorplan",
    "finished_basement": "Finished basement",
    "large_yard": "Spacious yard",
    "waterfront": "Waterfront feature",
}


def explain_listing(vector: FeatureVector, prefs: PreferenceVector, top_k: int = 3) -> List[str]:
    contributions: List[tuple[str, float]] = []
    for key, value in vector.numeric.items():
        weight = prefs.numeric.get(key)
        if weight:
            contributions.append((key, value * weight))
    for key, value in vector.tags.items():
        weight = prefs.tags.get(key)
        if weight and value:
            contributions.append((key, value * weight))
    contributions.sort(key=lambda item: abs(item[1]), reverse=True)
    explanations = []
    for key, score in contributions[:top_k]:
        label = LABEL_MAP.get(key, key)
        prefix = "✓" if score >= 0 else "–"
        explanations.append(f"{prefix} {label}")
    return explanations
