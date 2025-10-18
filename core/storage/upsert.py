from sqlalchemy.orm import Session
from core.storage.models import Listing
from datetime import datetime

def upsert_listing(db: Session, provider_id: int, listing_data: dict):
    """
    Inserts a new listing or updates an existing one based on 
    the unique constraint (provider_id, mls_id).
    
    Returns the created or updated Listing object.
    """
    mls_id = listing_data.get("mls_id")
    
    if not mls_id:
        # Should not happen if data is well-formed, but good practice to check
        print(f"Error: Listing data missing mls_id. Skipping.")
        return None

    # Check if a listing with this provider_id and mls_id already exists
    existing = (
        db.query(Listing)
        .filter(Listing.provider_id == provider_id)
        .filter(Listing.mls_id == mls_id)
        .first()
    )

    # Prepare data for insertion/update
    # We remove keys that are managed by the database or are not intended for direct update
    data_for_db = {k: v for k, v in listing_data.items() if k not in ['id', 'provider', 'listed_at']}
    data_for_db['provider_id'] = provider_id

    if existing:
        # Update existing listing
        data_for_db['updated_at'] = datetime.utcnow()
        for key, value in data_for_db.items():
            setattr(existing, key, value)
        return existing
    else:
        # Create new listing
        new_listing = Listing(**data_for_db)
        db.add(new_listing)
        return new_listing

# Note: This file intentionally does not call db.commit() 
# The caller (like ingest.py or seed.py) is responsible for committing the transaction.