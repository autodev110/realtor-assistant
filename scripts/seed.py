import sys
import os
from datetime import datetime

# Add the project root to the path to ensure imports work when running the script directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 🛑 FIX: Import 'Base' here to access the database metadata object.
from core.storage.db import SessionLocal, create_db_and_tables, engine
from core.storage.models import Provider, Client, Listing, Base
from core.storage.upsert import upsert_listing

# --- Mock Data ---

MOCK_PROVIDER = {
    "name": "mock_provider",
    "terms_url": "http://mock.terms",
    "license_notes": "Mock data, for testing only.",
}

MOCK_CLIENTS = [
    {
        "id": 1,
        "email": "dan@example.com",
        "name": "Dan",
        "stage": "active",
        "preferences": {"price_band": [400000, 700000], "area": ["Central City", "West Town"]},
        "taste_vector": {"num": {"list_price": -0.1, "sqft": 0.2, "hoa_fee": -0.5}, "tags": {"updated_kitchen": 0.5, "walkable": 0.3}},
        "tone_profile": "friendly",
    }
]

MOCK_LISTINGS = [
    {
        "mls_id": "L1001",
        "status": "Active",
        "property_type": "Single Family Residence",
        "street": "123 Mockingbird Ln",
        "city": "Central City",
        "state": "CA",
        "postal": "90210",
        "lat": 34.0,
        "lon": -118.0,
        "list_price": 550000.0,
        "beds": 4.0,
        "baths": 2.5,
        "sqft": 2800.0,
        "year_built": 1995,
        "hoa_fee": 150.0,
        "features": {"tags": ["updated_kitchen", "big_yard", "pool"]},
        "raw": {"source": "mock"},
    },
    {
        "mls_id": "L1002",
        "status": "ActiveUnderContract",
        "property_type": "Single Family Residence",
        "street": "456 Oak St",
        "city": "Eastside Boro",
        "state": "CA",
        "postal": "90211",
        "lat": 34.1,
        "lon": -118.1,
        "list_price": 425000.0,
        "beds": 3.0,
        "baths": 1.0,
        "sqft": 1500.0,
        "year_built": 1955,
        "hoa_fee": 0.0,
        "features": {"tags": ["finished_basement", "quiet_street"]},
        "raw": {"source": "mock"},
    },
    {
        "mls_id": "L1003",
        "status": "Active",
        "property_type": "Townhouse",
        "street": "789 Pine Ave",
        "city": "West Town",
        "state": "CA",
        "postal": "90212",
        "lat": 33.9,
        "lon": -117.9,
        "list_price": 495000.0,
        "beds": 3.0,
        "baths": 2.0,
        "sqft": 2200.0,
        "year_built": 2005,
        "hoa_fee": 50.0,
        "features": {"tags": ["walkable", "open_floorplan"]},
        "raw": {"source": "mock"},
    }
]

def get_or_create_provider(db, name, defaults=None):
    """Utility to get or create a provider entry."""
    provider = db.query(Provider).filter(Provider.name == name).first()
    if not provider:
        
        # 🛑 FIX: Copy the defaults, remove 'name' key, and use the rest.
        data = defaults.copy() if defaults else {}
        data.pop('name', None)  # Safely remove 'name' so it's not passed twice

        provider = Provider(name=name, **data)
        db.add(provider)
        db.commit()
        db.refresh(provider)
    return provider

def seed_db():
    """Drops existing tables, creates new ones, and inserts mock data."""
    print("Starting database seed...")
    
    # Drop and Create all tables (Ensures a clean slate for the SQLite quickstart)
    # 🛑 FIX: Use Base.metadata directly.
    Base.metadata.drop_all(bind=engine)
    create_db_and_tables()

    with SessionLocal() as db:
        # 1. Seed Provider
        provider = get_or_create_provider(db, MOCK_PROVIDER["name"], MOCK_PROVIDER)
        print(f"Seeded Provider: {provider.name}")

        # 2. Seed Clients
        for client_data in MOCK_CLIENTS:
            # We use an explicit ID=1 for quick testing
            client = db.query(Client).filter(Client.id == client_data["id"]).first()
            if not client:
                db.add(Client(**client_data))
        db.commit()
        print(f"Seeded {len(MOCK_CLIENTS)} clients.")

        # 3. Seed Listings
        for listing_data in MOCK_LISTINGS:
            # The upsert_listing function is assumed to handle the insertion
            # We use a dummy listed_at/updated_at value if not present
            listing_data.setdefault("listed_at", datetime.utcnow())
            listing_data.setdefault("updated_at", datetime.utcnow())
            upsert_listing(db, provider.id, listing_data)
        
        db.commit()
        print(f"Seeded {len(MOCK_LISTINGS)} listings.")
        print("Database seed successful.")

if __name__ == "__main__":
    seed_db()