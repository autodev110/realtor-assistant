from datetime import datetime, timedelta

from core.cma.engine import compute_cma
from core.schema.listing import NormalizedListing
from core.storage.upsert import upsert_listing


def create_listing(session, **kwargs):
    defaults = dict(
        provider="bright_mls",
        mls_id=str(kwargs.get("mls_id", datetime.utcnow().timestamp())),
        standard_status="Active",
        list_price=350000,
        address_line="101 Sample Rd",
        city="Norristown",
        state="PA",
        county="Montgomery",
        latitude=40.12,
        longitude=-75.34,
        beds=3,
        baths=2,
        sqft=1800,
        lot_sqft=6000,
        year_built=1992,
        listed_at=datetime.utcnow() - timedelta(days=3),
        source_updated_at=datetime.utcnow(),
    )
    defaults.update(kwargs)
    listing = NormalizedListing(**defaults)
    return upsert_listing(session, listing)


def test_compute_cma_identifies_deal(session):
    subject = create_listing(session, mls_id="SUBJECT", list_price=320000)

    comp1 = create_listing(
        session,
        mls_id="COMP1",
        standard_status="Closed",
        list_price=450000,
        close_price=440000,
        listed_at=datetime.utcnow() - timedelta(days=90),
        source_updated_at=datetime.utcnow() - timedelta(days=45),
        off_market_at=datetime.utcnow() - timedelta(days=45),
    )
    comp2 = create_listing(
        session,
        mls_id="COMP2",
        standard_status="Closed",
        list_price=460000,
        close_price=455000,
        listed_at=datetime.utcnow() - timedelta(days=80),
        source_updated_at=datetime.utcnow() - timedelta(days=30),
        off_market_at=datetime.utcnow() - timedelta(days=30),
        sqft=1900,
    )
    comp3 = create_listing(
        session,
        mls_id="COMP3",
        standard_status="Closed",
        list_price=470000,
        close_price=465000,
        listed_at=datetime.utcnow() - timedelta(days=100),
        source_updated_at=datetime.utcnow() - timedelta(days=25),
        off_market_at=datetime.utcnow() - timedelta(days=25),
        beds=4,
    )

    comparables = [
        (comp1, 0.4, 45),
        (comp2, 0.6, 30),
        (comp3, 0.55, 25),
    ]

    result = compute_cma(subject, comparables)
    assert result.price_mid_cents > 40000000
    assert result.deal_alert is not None
    assert result.deal_alert.discount_ratio < 0.8
    assert len(result.comps) == 3
