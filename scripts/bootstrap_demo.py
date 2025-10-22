from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import List

from core.storage.db import engine, init_db, session_scope
from core.storage.models import Base, Client, Interaction
from core.storage.upsert import upsert_listing
from core.schema.listing import NormalizedListing
from apps.workers.tasks import generate_client_digest


def reset_database():
    Base.metadata.drop_all(bind=engine)
    init_db()


def seed_clients(session) -> Client:
    client = Client(
        full_name="Dan Realtor",
        email="dan@example.com",
        phone="555-111-2222",
        prefs={
            "price_min": 300000,
            "price_max": 550000,
            "beds_min": 3,
            "baths_min": 2,
            "counties": ["Montgomery", "Chester"],
        },
        tone_profile={"formality": "conversational", "verbosity": "detailed", "signoff": "Cheers"},
        auto_send_enabled=False,
    )
    session.add(client)
    session.flush()
    return client


def seed_listings(session) -> List[str]:
    now = datetime.utcnow()
    listings = [
        NormalizedListing(
            provider="bright_mls",
            mls_id="BRG-1001",
            standard_status="Active",
            list_price=325000,
            address_line="123 Market St",
            city="Norristown",
            state="PA",
            postal_code="19401",
            county="Montgomery",
            latitude=40.121,
            longitude=-75.341,
            beds=3,
            baths=2,
            sqft=1820,
            lot_sqft=5800,
            year_built=1992,
            amenities={"garage": True, "walkscore": 65},
            features=["finished_basement", "open_floorplan"],
            listed_at=now - timedelta(days=3),
            source_updated_at=now,
        ),
        NormalizedListing(
            provider="attom",
            external_id="ATT-2002",
            standard_status="Active",
            list_price=489000,
            address_line="880 Valley Rd",
            city="Downingtown",
            state="PA",
            postal_code="19335",
            county="Chester",
            latitude=40.022,
            longitude=-75.703,
            beds=4,
            baths=2.5,
            sqft=2400,
            lot_sqft=9000,
            year_built=2006,
            amenities={"garage": True, "pool": False},
            listed_at=now - timedelta(days=5),
            source_updated_at=now,
        ),
        NormalizedListing(
            provider="rpr",
            mls_id="RPR-3003",
            standard_status="Active",
            list_price=410000,
            address_line="77 Creekside Ln",
            city="Pottstown",
            state="PA",
            postal_code="19464",
            county="Montgomery",
            latitude=40.249,
            longitude=-75.644,
            beds=3,
            baths=2.5,
            sqft=2050,
            lot_sqft=7200,
            year_built=2004,
            amenities={"garage": True, "walkscore": 55},
            features=["open_floorplan"],
            listed_at=now - timedelta(days=2),
            source_updated_at=now,
        ),
        # Comparable closed sales
        NormalizedListing(
            provider="bright_mls",
            mls_id="BRG-CL-1",
            standard_status="Closed",
            close_price=460000,
            list_price=450000,
            address_line="21 Willow Ct",
            city="Norristown",
            state="PA",
            postal_code="19403",
            county="Montgomery",
            latitude=40.123,
            longitude=-75.337,
            beds=3,
            baths=2.5,
            sqft=1900,
            lot_sqft=6100,
            year_built=1995,
            amenities={"garage": True},
            listed_at=now - timedelta(days=70),
            source_updated_at=now - timedelta(days=15),
            off_market_at=now - timedelta(days=15),
        ),
        NormalizedListing(
            provider="bright_mls",
            mls_id="BRG-CL-2",
            standard_status="Closed",
            close_price=480000,
            list_price=470000,
            address_line="89 Juniper Dr",
            city="Norristown",
            state="PA",
            postal_code="19401",
            county="Montgomery",
            latitude=40.118,
            longitude=-75.352,
            beds=3,
            baths=3,
            sqft=2000,
            lot_sqft=6200,
            year_built=1990,
            amenities={"garage": True, "pool": True},
            listed_at=now - timedelta(days=90),
            source_updated_at=now - timedelta(days=25),
            off_market_at=now - timedelta(days=25),
        ),
        NormalizedListing(
            provider="bright_mls",
            mls_id="BRG-CL-3",
            standard_status="Closed",
            close_price=475000,
            list_price=465000,
            address_line="66 Elm St",
            city="Norristown",
            state="PA",
            postal_code="19401",
            county="Montgomery",
            latitude=40.125,
            longitude=-75.345,
            beds=3,
            baths=2,
            sqft=1750,
            lot_sqft=5400,
            year_built=1988,
            amenities={"garage": True},
            listed_at=now - timedelta(days=110),
            source_updated_at=now - timedelta(days=40),
            off_market_at=now - timedelta(days=40),
        ),
    ]

    listing_ids = []
    for listing in listings:
        record = upsert_listing(session, listing)
        session.flush()
        listing_ids.append(str(record.id))
    return listing_ids


def create_sample_interactions(session, client: Client, listing_ids: List[str]) -> None:
    if not listing_ids:
        return
    interaction = Interaction(
        client_id=client.id,
        listing_id=uuid.UUID(listing_ids[0]),
        interaction_type="like",
        metadata={"signal": 5.0},
    )
    session.add(interaction)


def main():
    reset_database()
    with session_scope() as session:
        client = seed_clients(session)
        listing_ids = seed_listings(session)
        create_sample_interactions(session, client, listing_ids)
        session.commit()

    with session_scope() as session:
        client = session.query(Client).first()
        if client:
            generate_client_digest(session, client, limit=3)
            session.commit()

    print("Demo data populated. Run `uvicorn apps.api.main:app --reload` to try the API.")


if __name__ == "__main__":
    main()
