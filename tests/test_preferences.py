from datetime import datetime, timedelta

from core.matching.preferences import (
    PreferenceVector,
    apply_feedback,
    score_listing,
    vector_from_listing,
)
from core.storage.models import Listing


def build_listing(**kwargs):
    listing = Listing(
        provider="bright_mls",
        source_type="mls",
        mls_id=kwargs.get("mls_id", "TEST"),
        dedupe_key="test|listing",
        standard_status="Active",
        address_line="123 Demo",
        city="Norristown",
        state="PA",
        list_price_cents=kwargs.get("list_price_cents", 35000000),
        beds=kwargs.get("beds", 3),
        baths=kwargs.get("baths", 2),
        sqft=kwargs.get("sqft", 1800),
        lot_sqft=kwargs.get("lot_sqft", 5000),
        year_built=kwargs.get("year_built", 1992),
        amenities={"garage": True, "walkscore": 70},
    )
    return listing


def test_preference_learning_increases_score(session, client):
    listing = build_listing()
    vector = vector_from_listing(listing, client.prefs)
    prefs = PreferenceVector()

    baseline = score_listing(vector, prefs)
    assert baseline == 0.0

    apply_feedback(prefs, vector, signal_strength=1.0)
    improved = score_listing(vector, prefs)
    assert improved > baseline

    apply_feedback(prefs, vector, signal_strength=-1.0)
    reduced = score_listing(vector, prefs)
    assert reduced < improved
