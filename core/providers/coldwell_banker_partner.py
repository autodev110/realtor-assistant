from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterator, Optional

from core.schema.listing import NormalizedListing

from .base import ProviderClient
from .utils import parse_datetime, to_float, to_int


class ColdwellBankerPartnerClient(ProviderClient):
    """Stub client for Coldwell Banker brokerage data feed."""

    name = "coldwell_banker_partner"

    def fetch_updated(
        self, since: Optional[datetime] = None, cursor: Optional[str] = None
    ) -> Iterator[Dict]:
        yield from self._sample_payload()

    def normalize(self, raw: Dict) -> NormalizedListing:
        address = raw.get("address", {})
        return NormalizedListing(
            provider=self.name,
            external_id=raw.get("listing_id"),
            url=raw.get("listing_url"),
            address_line=address.get("street"),
            city=address.get("city"),
            state=address.get("state"),
            postal_code=address.get("zip"),
            county=address.get("county"),
            latitude=to_float(address.get("lat")),
            longitude=to_float(address.get("lng")),
            standard_status=raw.get("status") or "Active",
            property_type=raw.get("property_type"),
            list_price=to_float(raw.get("list_price")),
            beds=to_float(raw.get("beds")),
            baths=to_float(raw.get("baths")),
            sqft=to_int(raw.get("square_feet")),
            lot_sqft=to_int(raw.get("lot_square_feet")),
            year_built=to_int(raw.get("year_built")),
            amenities=raw.get("amenities", {}),
            remarks=raw.get("remarks"),
            provider_flags={
                "redistribution_allowed": raw.get("allow_syndication", False),
                "photo_reuse_allowed": raw.get("allow_photo_reuse", False),
            },
            listed_at=parse_datetime(raw.get("list_date")),
            source_updated_at=parse_datetime(raw.get("updated_at")),
            source_payload=raw,
        )

    def _sample_payload(self) -> Iterator[Dict]:
        yield {
            "listing_id": "CBPA-0001",
            "listing_url": "https://www.coldwellbankerhomes.com/CBPA-0001",
            "status": "Active",
            "property_type": "Single Family",
            "list_price": 615000,
            "beds": 4,
            "baths": 3,
            "square_feet": 2800,
            "lot_square_feet": 10000,
            "year_built": 2001,
            "address": {
                "street": "88 Meadow Ln",
                "city": "Downingtown",
                "state": "PA",
                "zip": "19335",
                "county": "Chester",
                "lat": 40.017,
                "lng": -75.704,
            },
            "list_date": datetime.utcnow().isoformat(),
        }
